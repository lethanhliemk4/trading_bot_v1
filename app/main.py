import asyncio
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI

from app.api.health import router as health_router
from app.config import get_settings
from app.logger import configure_logging
from app.telegram.bot import create_bot, send_message
from app.market.ws_client import stream_btc_trades
from app.market.scanner import scan_market
from app.db.session import engine, Base
import app.db.models
from app.services.signal_service import (
    save_signal,
    get_pending_signals,
    update_performance,
)
from app.services.market_price_service import get_symbol_price
from app.services.ai_filter import ai_filter_signal
from app.services.strategy_service import build_strategy
from app.services.risk_service import (
    build_risk_plan,
    is_live_daily_loss_limit_hit,
)
from app.services.trade_mode_service import get_trade_mode, panic_stop
from app.services.paper_trade_service import (
    create_paper_trade,
    get_open_paper_trades,
    close_paper_trade,
    partial_close_paper_trade_tp1,
    activate_paper_trade_trailing,
    update_paper_trade_trailing_sl,
    is_daily_loss_limit_hit,
)
from app.services.live_trade_service import (
    execute_live_market_order,
    get_open_live_trades,
    mark_live_trade_tp1_hit,
    activate_live_trade_trailing,
    update_live_trade_trailing_sl,
    close_live_trade,
    sync_open_live_trades,
    execute_live_close_market_order,
)

settings = get_settings()
configure_logging()
logger = logging.getLogger(__name__)

telegram_app = None
market_task = None
scanner_task = None
performance_task = None
paper_trade_task = None
live_trade_task = None
heartbeat_task = None
watchdog_task = None

last_alerts = {}
daily_loss_alert_sent = False
live_daily_loss_alert_sent = False
live_error_count = 0
LIVE_MAX_CONSECUTIVE_ERRORS = 5
live_last_trade_time = 0
LIVE_TRADE_COOLDOWN_SECONDS = getattr(settings, "LIVE_TRADE_COOLDOWN_SECONDS", 60)
HEARTBEAT_INTERVAL_SECONDS = getattr(settings, "HEARTBEAT_INTERVAL_SECONDS", 300)
WATCHDOG_INTERVAL_SECONDS = getattr(settings, "WATCHDOG_INTERVAL_SECONDS", 60)
LOOP_STALE_THRESHOLD_SECONDS = getattr(settings, "LOOP_STALE_THRESHOLD_SECONDS", 600)

scanner_loop_last_seen = 0.0
paper_trade_loop_last_seen = 0.0
live_trade_loop_last_seen = 0.0
performance_loop_last_seen = 0.0

scanner_stale_alert_sent = False
paper_trade_stale_alert_sent = False
live_trade_stale_alert_sent = False
performance_stale_alert_sent = False

SIGNAL_CHECK_AFTER_5M_SECONDS = 300
SIGNAL_CHECK_AFTER_15M_SECONDS = 900


def format_market_message(results):
    lines = ["🚀 SCANNER ALERT", ""]

    for coin in results:
        score = coin["score"]
        change = coin["price_change_5m"]
        vol = coin["quote_volume_5m"] / 1_000_000
        spike = coin["volume_spike_ratio"]
        side = coin.get("side", "LONG")

        if score >= 80:
            tag = "🔥🔥"
        elif score >= 60:
            tag = "🔥"
        else:
            tag = "📈"

        lines.append(f"{tag} {coin['symbol']} | {side} | Score: {score}")
        lines.append(f"   5m: {change:+.2f}% | Vol: {vol:.2f}M | Spike: x{spike:.2f}")

        ai = coin.get("ai")
        if ai:
            lines.append(f"   🤖 AI: {ai['confidence']:.0f}% - {ai['reason']}")

        strategy = coin.get("strategy")
        if strategy:
            lines.append(f"   📏 ATR: {strategy['atr']:.6f}")
            lines.append(f"   🎯 Entry: {strategy['entry']:.6f}")
            lines.append(f"   🛑 SL: {strategy['sl']:.6f}")
            lines.append(f"   🎯 TP1: {strategy['tp1']:.6f}")
            lines.append(f"   🚀 TP2: {strategy['tp2']:.6f}")
            lines.append(f"   ⚖️ RR: 1:{strategy['rr']:.2f}")

        risk = coin.get("risk")
        if risk:
            lines.append(f"   💰 Capital: {risk['capital']:.2f} USDT")
            lines.append(f"   ⚠️ Risk: {risk['risk_percent']:.2f}% = {risk['risk_amount']:.2f} USDT")
            lines.append(f"   📦 Position Size: {risk['position_size']:.6f}")
            lines.append(f"   💵 Notional: {risk['notional']:.2f} USDT")

        lines.append("")

    return "\n".join(lines).strip()


def format_performance_message(symbol: str, result_percent: float, status: str, label: str) -> str:
    icon = "✅"
    if status == "lose":
        icon = "❌"
    elif status == "draw":
        icon = "➖"

    return (
        f"{icon} SIGNAL RESULT\n\n"
        f"{symbol} | {label} | {status.upper()} | {result_percent:+.2f}%"
    )


def format_paper_open_message(symbol: str, side: str, entry: float, sl: float, tp2: float) -> str:
    return (
        "🧪 PAPER TRADE OPENED\n\n"
        f"{symbol} | {side}\n"
        f"Entry: {entry:.6f}\n"
        f"SL: {sl:.6f}\n"
        f"TP2: {tp2:.6f}"
    )


def format_paper_tp1_partial_message(symbol: str, price: float, close_ratio: float, realized_pnl: float) -> str:
    return (
        "🟡 PAPER TRADE TP1 PARTIAL CLOSE\n\n"
        f"{symbol}\n"
        f"Price: {price:.6f}\n"
        f"Closed: {close_ratio * 100:.0f}%\n"
        f"Realized PnL: {realized_pnl:+.6f}\n"
        "Trailing activated on remaining position"
    )


def format_paper_trailing_message(symbol: str, trailing_sl: float) -> str:
    return (
        "🛡 PAPER TRADE TRAILING UPDATED\n\n"
        f"{symbol}\n"
        f"Trailing SL: {trailing_sl:.6f}"
    )


def format_paper_close_message(symbol: str, reason: str, exit_price: float, result_percent: float) -> str:
    return (
        "🧪 PAPER TRADE CLOSED\n\n"
        f"{symbol}\n"
        f"Reason: {reason}\n"
        f"Exit: {exit_price:.6f}\n"
        f"Result: {result_percent:+.2f}%"
    )


def format_daily_loss_breaker_message(today_pnl: float) -> str:
    return (
        "🛑 DAILY LOSS CIRCUIT BREAKER\n\n"
        f"Today PnL: {today_pnl:+.2f} USDT\n"
        f"Limit: -{abs(settings.DAILY_LOSS_LIMIT_USDT):.2f} USDT\n\n"
        "Paper trading has been stopped automatically."
    )


def format_live_open_message(symbol: str, side: str, qty: float) -> str:
    return (
        "🚨 LIVE TRADE EXECUTED\n\n"
        f"{symbol} | {side}\n"
        f"Qty: {qty:.8f}\n"
        f"Env: {'TESTNET' if settings.BINANCE_USE_TESTNET else 'MAINNET'}"
    )


def format_live_fail_message(symbol: str, stage: str, reason: str) -> str:
    return (
        "❌ LIVE TRADE FAILED\n\n"
        f"{symbol}\n"
        f"Stage: {stage}\n"
        f"Reason: {reason}\n"
        f"Env: {'TESTNET' if settings.BINANCE_USE_TESTNET else 'MAINNET'}"
    )


def format_live_tp1_message(symbol: str, price: float) -> str:
    return (
        "🟡 LIVE TRADE TP1 HIT\n\n"
        f"{symbol}\n"
        f"Price: {price:.6f}\n"
        "Trailing activated\n"
        f"Env: {'TESTNET' if settings.BINANCE_USE_TESTNET else 'MAINNET'}"
    )


def format_live_trailing_message(symbol: str, trailing_sl: float) -> str:
    return (
        "🛡 LIVE TRADE TRAILING UPDATED\n\n"
        f"{symbol}\n"
        f"Trailing SL: {trailing_sl:.6f}\n"
        f"Env: {'TESTNET' if settings.BINANCE_USE_TESTNET else 'MAINNET'}"
    )


def format_live_close_message(symbol: str, reason: str, exit_price: float, result_percent: float) -> str:
    return (
        "🚨 LIVE TRADE CLOSED\n\n"
        f"{symbol}\n"
        f"Reason: {reason}\n"
        f"Exit: {exit_price:.6f}\n"
        f"Result: {result_percent:+.2f}%\n"
        f"Env: {'TESTNET' if settings.BINANCE_USE_TESTNET else 'MAINNET'}"
    )


def format_live_daily_loss_breaker_message(today_pnl: float) -> str:
    return (
        "🛑 LIVE DAILY LOSS CIRCUIT BREAKER\n\n"
        f"Today LIVE PnL: {today_pnl:+.2f} USDT\n"
        f"Limit: -{abs(settings.LIVE_DAILY_LOSS_LIMIT_USDT):.2f} USDT\n\n"
        "LIVE trading has been stopped automatically."
    )


def format_live_error_breaker_message(error_count: int) -> str:
    return (
        "🚨 LIVE ERROR CIRCUIT BREAKER\n\n"
        f"Consecutive Errors: {error_count}\n"
        f"Threshold: {LIVE_MAX_CONSECUTIVE_ERRORS}\n\n"
        "LIVE trading has been stopped automatically."
    )


def format_heartbeat_message() -> str:
    return (
        "💓 BOT HEARTBEAT\n\n"
        f"Env: {settings.APP_ENV}\n"
        f"Mode: {settings.APP_MODE}\n"
        f"KILL_SWITCH: {settings.KILL_SWITCH}"
    )


def format_watchdog_alert_message(loop_name: str, age_seconds: float) -> str:
    return (
        "🚨 LOOP WATCHDOG ALERT\n\n"
        f"Loop: {loop_name}\n"
        f"Last seen: {age_seconds:.1f}s ago\n"
        f"Threshold: {LOOP_STALE_THRESHOLD_SECONDS}s\n\n"
        "Loop may be stale or blocked."
    )


def _get_live_effective_entry_price(trade) -> float:
    avg_fill_price = float(trade.avg_fill_price or 0.0)
    if avg_fill_price > 0:
        return avg_fill_price
    return float(trade.entry_price or 0.0)


def _has_live_executed_position(trade) -> bool:
    executed_qty = float(trade.executed_qty or 0.0)
    remaining_qty = float(trade.remaining_qty or 0.0)
    return executed_qty > 0 or remaining_qty > 0


async def scanner_loop():
    global telegram_app, last_alerts, live_last_trade_time, scanner_loop_last_seen, scanner_stale_alert_sent

    while True:
        scanner_loop_last_seen = time.time()
        scanner_stale_alert_sent = False

        try:
            if settings.KILL_SWITCH:
                logger.warning("KILL_SWITCH active, scanner paused")
                await asyncio.sleep(settings.SCAN_INTERVAL_SECONDS)
                continue

            if settings.is_test_mode:
                logger.info("🔥 Scanner running (TEST MODE)...")
            else:
                logger.info("Scanner running...")

            results = await scan_market()
            logger.info("Found %s coins", len(results))

            now = time.time()
            new_alerts = []

            for coin in results:
                symbol = coin["symbol"]
                score = coin["score"]

                if settings.is_test_mode:
                    cooldown = settings.TEST_MODE_COOLDOWN_SECONDS
                else:
                    cooldown = settings.ALERT_COOLDOWN_SECONDS
                    if score >= 80:
                        cooldown = 300
                    elif score >= 60:
                        cooldown = 600

                last_time = last_alerts.get(symbol)

                if last_time is not None and now - last_time <= cooldown:
                    logger.debug("Cooldown skip %s", symbol)
                    continue

                ai_result = ai_filter_signal(coin)
                if not ai_result:
                    logger.info("AI skipped %s", symbol)
                    continue

                coin["ai"] = ai_result
                coin["strategy"] = build_strategy(coin)

                risk = build_risk_plan(coin["strategy"])
                if not risk:
                    logger.warning("Risk rejected %s", symbol)
                    continue

                coin["risk"] = risk
                new_alerts.append(coin)
                last_alerts[symbol] = now

            logger.info("🚀 Sending %s alerts", len(new_alerts))

            if new_alerts:
                msg = format_market_message(new_alerts)
                await send_message(telegram_app, msg)

                mode = get_trade_mode()
                open_paper_trades = get_open_paper_trades()
                open_paper_symbols = {trade.symbol.upper() for trade in open_paper_trades}

                open_live_trades = get_open_live_trades(limit=500)
                open_live_symbols = {trade.symbol.upper() for trade in open_live_trades}

                for coin in new_alerts:
                    save_signal(coin)

                    if mode["trade_mode"] == "PAPER" and mode["auto_trade_enabled"]:
                        if coin["symbol"].upper() in open_paper_symbols:
                            logger.info("Skip duplicate paper trade for %s", coin["symbol"])
                            continue

                        trade = create_paper_trade({
                            "symbol": coin["symbol"],
                            "side": coin["strategy"]["side"],
                            "entry_price": coin["strategy"]["entry"],
                            "sl": coin["strategy"]["sl"],
                            "tp1": coin["strategy"]["tp1"],
                            "tp2": coin["strategy"]["tp2"],
                            "rr": coin["strategy"]["rr"],
                            "risk_amount": coin["risk"]["risk_amount"],
                            "position_size": coin["risk"]["position_size"],
                            "notional": coin["risk"]["notional"],
                        })

                        if not trade:
                            logger.warning("Create paper trade failed %s", coin["symbol"])
                            continue

                        open_paper_symbols.add(coin["symbol"].upper())

                        await send_message(
                            telegram_app,
                            format_paper_open_message(
                                trade.symbol,
                                trade.side,
                                trade.entry_price,
                                trade.sl,
                                trade.tp2,
                            ),
                        )

                    elif mode["trade_mode"] == "LIVE" and mode["auto_trade_enabled"]:
                        if coin["symbol"].upper() in open_live_symbols:
                            logger.info("Skip duplicate live trade for %s", coin["symbol"])
                            continue

                        now_ts = time.time()
                        if now_ts - live_last_trade_time < LIVE_TRADE_COOLDOWN_SECONDS:
                            logger.info(
                                "LIVE COOLDOWN ACTIVE | skip %s | remaining=%.1fs",
                                coin["symbol"],
                                LIVE_TRADE_COOLDOWN_SECONDS - (now_ts - live_last_trade_time),
                            )
                            continue

                        try:
                            logger.info("🚨 LIVE TRADE TRIGGER %s", coin["symbol"])

                            result = await execute_live_market_order(
                                coin["strategy"],
                                coin["risk"],
                            )

                            if not result["ok"]:
                                logger.warning(
                                    "LIVE TRADE FAILED %s | stage=%s | reason=%s",
                                    coin["symbol"],
                                    result.get("stage"),
                                    result.get("reason"),
                                )

                                await send_message(
                                    telegram_app,
                                    format_live_fail_message(
                                        coin["symbol"],
                                        str(result.get("stage", "unknown")),
                                        str(result.get("reason", "unknown error")),
                                    ),
                                )
                                continue

                            live_last_trade_time = time.time()
                            open_live_symbols.add(coin["symbol"].upper())

                            await send_message(
                                telegram_app,
                                format_live_open_message(
                                    coin["symbol"],
                                    coin["strategy"]["side"],
                                    float(result.get("qty", 0.0)),
                                ),
                            )

                        except Exception as e:
                            logger.exception("LIVE TRADE ERROR %s: %s", coin["symbol"], e)
                            await send_message(
                                telegram_app,
                                format_live_fail_message(
                                    coin["symbol"],
                                    "exception",
                                    str(e),
                                ),
                            )

                logger.info("✅ Sent %s alerts to Telegram + DB", len(new_alerts))

        except Exception as e:
            logger.exception("Scanner loop error: %s", e)

        await asyncio.sleep(settings.SCAN_INTERVAL_SECONDS)


async def paper_trade_loop():
    global telegram_app, daily_loss_alert_sent, paper_trade_loop_last_seen, paper_trade_stale_alert_sent

    while True:
        paper_trade_loop_last_seen = time.time()
        paper_trade_stale_alert_sent = False

        try:
            if settings.KILL_SWITCH:
                logger.warning("KILL_SWITCH active, paper trade loop paused")
                await asyncio.sleep(settings.PAPER_TRADE_CHECK_INTERVAL_SECONDS)
                continue

            mode = get_trade_mode()
            if mode["trade_mode"] != "PAPER" or not mode["auto_trade_enabled"]:
                daily_loss_alert_sent = False
                await asyncio.sleep(settings.PAPER_TRADE_CHECK_INTERVAL_SECONDS)
                continue

            limit_hit, today_pnl = is_daily_loss_limit_hit()
            if limit_hit:
                if not daily_loss_alert_sent:
                    logger.warning("Daily loss limit hit | pnl=%s", today_pnl)

                    state = panic_stop()

                    await send_message(
                        telegram_app,
                        format_daily_loss_breaker_message(today_pnl),
                    )

                    logger.warning(
                        "Paper mode stopped by daily loss breaker | mode=%s",
                        state["trade_mode"],
                    )

                    daily_loss_alert_sent = True

                await asyncio.sleep(settings.PAPER_TRADE_CHECK_INTERVAL_SECONDS)
                continue

            trades = get_open_paper_trades()

            for trade in trades:
                price = await get_symbol_price(trade.symbol)
                if not price:
                    continue

                if trade.entry_price <= 0:
                    logger.warning(
                        "Skip invalid entry_price | trade_id=%s | entry=%s",
                        trade.id,
                        trade.entry_price,
                    )
                    continue

                if trade.side == "LONG":
                    result_percent = ((price - trade.entry_price) / trade.entry_price) * 100

                    if abs(result_percent) > 100:
                        logger.warning(
                            "Skip abnormal LONG result | trade_id=%s | entry=%s | price=%s | result=%s",
                            trade.id,
                            trade.entry_price,
                            price,
                            result_percent,
                        )
                        continue

                    if not trade.tp1_hit and price >= trade.tp1:
                        partial = partial_close_paper_trade_tp1(trade.id, price, 0.5)
                        if partial:
                            activated = activate_paper_trade_trailing(trade.id, trade.entry_price)
                            if activated:
                                trade.tp1_hit = partial.tp1_hit
                                trade.trailing_active = activated.trailing_active
                                trade.trailing_sl = activated.trailing_sl
                                trade.remaining_size = partial.remaining_size
                                trade.realized_pnl = partial.realized_pnl

                            await send_message(
                                telegram_app,
                                format_paper_tp1_partial_message(
                                    trade.symbol,
                                    price,
                                    0.5,
                                    partial.realized_pnl,
                                ),
                            )
                        continue

                    if trade.trailing_active:
                        current_trailing = trade.trailing_sl if trade.trailing_sl is not None else trade.entry_price
                        new_trailing_sl = max(current_trailing, price * 0.995)

                        if new_trailing_sl > current_trailing:
                            updated = update_paper_trade_trailing_sl(trade.id, new_trailing_sl)
                            if updated:
                                trade.trailing_sl = updated.trailing_sl
                                await send_message(
                                    telegram_app,
                                    format_paper_trailing_message(trade.symbol, updated.trailing_sl),
                                )

                        effective_sl = trade.trailing_sl if trade.trailing_sl is not None else trade.entry_price
                    else:
                        effective_sl = trade.sl

                    if price <= effective_sl:
                        reason = "TSL" if trade.trailing_active else "SL"
                        closed = close_paper_trade(trade.id, price, result_percent, reason)
                        if closed:
                            await send_message(
                                telegram_app,
                                format_paper_close_message(
                                    trade.symbol,
                                    reason,
                                    price,
                                    result_percent,
                                ),
                            )

                    elif price >= trade.tp2:
                        closed = close_paper_trade(trade.id, price, result_percent, "TP2")
                        if closed:
                            await send_message(
                                telegram_app,
                                format_paper_close_message(
                                    trade.symbol,
                                    "TP2",
                                    price,
                                    result_percent,
                                ),
                            )

                else:
                    result_percent = ((trade.entry_price - price) / trade.entry_price) * 100

                    if abs(result_percent) > 100:
                        logger.warning(
                            "Skip abnormal SHORT result | trade_id=%s | entry=%s | price=%s | result=%s",
                            trade.id,
                            trade.entry_price,
                            price,
                            result_percent,
                        )
                        continue

                    if not trade.tp1_hit and price <= trade.tp1:
                        partial = partial_close_paper_trade_tp1(trade.id, price, 0.5)
                        if partial:
                            activated = activate_paper_trade_trailing(trade.id, trade.entry_price)
                            if activated:
                                trade.tp1_hit = partial.tp1_hit
                                trade.trailing_active = activated.trailing_active
                                trade.trailing_sl = activated.trailing_sl
                                trade.remaining_size = partial.remaining_size
                                trade.realized_pnl = partial.realized_pnl

                            await send_message(
                                telegram_app,
                                format_paper_tp1_partial_message(
                                    trade.symbol,
                                    price,
                                    0.5,
                                    partial.realized_pnl,
                                ),
                            )
                        continue

                    if trade.trailing_active:
                        current_trailing = trade.trailing_sl if trade.trailing_sl is not None else trade.entry_price
                        new_trailing_sl = min(current_trailing, price * 1.005)

                        if new_trailing_sl < current_trailing:
                            updated = update_paper_trade_trailing_sl(trade.id, new_trailing_sl)
                            if updated:
                                trade.trailing_sl = updated.trailing_sl
                                await send_message(
                                    telegram_app,
                                    format_paper_trailing_message(trade.symbol, updated.trailing_sl),
                                )

                        effective_sl = trade.trailing_sl if trade.trailing_sl is not None else trade.entry_price
                    else:
                        effective_sl = trade.sl

                    if price >= effective_sl:
                        reason = "TSL" if trade.trailing_active else "SL"
                        closed = close_paper_trade(trade.id, price, result_percent, reason)
                        if closed:
                            await send_message(
                                telegram_app,
                                format_paper_close_message(
                                    trade.symbol,
                                    reason,
                                    price,
                                    result_percent,
                                ),
                            )

                    elif price <= trade.tp2:
                        closed = close_paper_trade(trade.id, price, result_percent, "TP2")
                        if closed:
                            await send_message(
                                telegram_app,
                                format_paper_close_message(
                                    trade.symbol,
                                    "TP2",
                                    price,
                                    result_percent,
                                ),
                            )

        except Exception as e:
            logger.exception("Paper trade loop error: %s", e)

        await asyncio.sleep(settings.PAPER_TRADE_CHECK_INTERVAL_SECONDS)


async def live_trade_loop():
    global telegram_app, live_daily_loss_alert_sent, live_error_count, live_trade_loop_last_seen, live_trade_stale_alert_sent

    while True:
        live_trade_loop_last_seen = time.time()
        live_trade_stale_alert_sent = False

        try:
            if settings.KILL_SWITCH:
                logger.warning("KILL_SWITCH active, live trade loop paused")
                await asyncio.sleep(settings.PAPER_TRADE_CHECK_INTERVAL_SECONDS)
                continue

            mode = get_trade_mode()
            if mode["trade_mode"] != "LIVE" or not mode["auto_trade_enabled"]:
                live_daily_loss_alert_sent = False
                live_error_count = 0
                await asyncio.sleep(settings.PAPER_TRADE_CHECK_INTERVAL_SECONDS)
                continue

            live_limit_hit, live_today_pnl = is_live_daily_loss_limit_hit()
            if live_limit_hit:
                if not live_daily_loss_alert_sent:
                    logger.warning("LIVE daily loss limit hit | pnl=%s", live_today_pnl)

                    state = panic_stop()

                    await send_message(
                        telegram_app,
                        format_live_daily_loss_breaker_message(live_today_pnl),
                    )

                    logger.warning(
                        "Live mode stopped by daily loss breaker | mode=%s",
                        state["trade_mode"],
                    )

                    live_daily_loss_alert_sent = True

                await asyncio.sleep(settings.PAPER_TRADE_CHECK_INTERVAL_SECONDS)
                continue

            try:
                synced_ids = await sync_open_live_trades()
                if synced_ids:
                    logger.info("Synced %s open live trades from Binance", len(synced_ids))
                live_error_count = 0
            except Exception as e:
                logger.exception("Live trade sync error: %s", e)

                live_error_count += 1

                if live_error_count >= LIVE_MAX_CONSECUTIVE_ERRORS:
                    state = panic_stop()

                    await send_message(
                        telegram_app,
                        format_live_error_breaker_message(live_error_count),
                    )

                    logger.warning(
                        "Live stopped by error breaker | mode=%s",
                        state["trade_mode"],
                    )

                    live_error_count = 0
                    await asyncio.sleep(settings.PAPER_TRADE_CHECK_INTERVAL_SECONDS)
                    continue

            trades = get_open_live_trades()

            for trade in trades:
                if not _has_live_executed_position(trade):
                    logger.info(
                        "Skip live management until executed qty exists | trade_id=%s | symbol=%s",
                        trade.id,
                        trade.symbol,
                    )
                    continue

                price = await get_symbol_price(trade.symbol)
                if not price:
                    continue

                effective_entry_price = _get_live_effective_entry_price(trade)
                if effective_entry_price <= 0:
                    logger.warning(
                        "Skip invalid live effective entry | trade_id=%s | entry=%s | avg_fill=%s",
                        trade.id,
                        trade.entry_price,
                        trade.avg_fill_price,
                    )
                    continue

                if trade.side == "LONG":
                    result_percent = ((price - effective_entry_price) / effective_entry_price) * 100

                    if abs(result_percent) > 100:
                        logger.warning(
                            "Skip abnormal LIVE LONG result | trade_id=%s | entry=%s | price=%s | result=%s",
                            trade.id,
                            effective_entry_price,
                            price,
                            result_percent,
                        )
                        continue

                    if not trade.tp1_hit and price >= trade.tp1:
                        marked = mark_live_trade_tp1_hit(trade.id)
                        if marked:
                            activated = activate_live_trade_trailing(trade.id, effective_entry_price)
                            if activated:
                                trade.tp1_hit = marked.tp1_hit
                                trade.trailing_active = activated.trailing_active
                                trade.trailing_sl = activated.trailing_sl

                            await send_message(
                                telegram_app,
                                format_live_tp1_message(
                                    trade.symbol,
                                    price,
                                ),
                            )
                        continue

                    if trade.trailing_active:
                        current_trailing = trade.trailing_sl if trade.trailing_sl is not None else effective_entry_price
                        new_trailing_sl = max(current_trailing, price * 0.995)

                        if new_trailing_sl > current_trailing:
                            updated = update_live_trade_trailing_sl(trade.id, new_trailing_sl)
                            if updated:
                                trade.trailing_sl = updated.trailing_sl
                                await send_message(
                                    telegram_app,
                                    format_live_trailing_message(trade.symbol, updated.trailing_sl),
                                )

                        effective_sl = trade.trailing_sl if trade.trailing_sl is not None else effective_entry_price
                    else:
                        effective_sl = trade.sl

                    if price <= effective_sl:
                        reason = "TSL" if trade.trailing_active else "SL"
                        closed_result = await execute_live_close_market_order(trade.id)
                        if closed_result.get("ok"):
                            await send_message(
                                telegram_app,
                                format_live_close_message(
                                    trade.symbol,
                                    reason,
                                    float(closed_result.get("exit_price", price)),
                                    float(closed_result.get("result_percent", result_percent)),
                                ),
                            )
                        else:
                            logger.warning(
                                "LIVE CLOSE FAILED %s | trade_id=%s | stage=%s | reason=%s",
                                trade.symbol,
                                trade.id,
                                closed_result.get("stage"),
                                closed_result.get("reason"),
                            )
                            await send_message(
                                telegram_app,
                                format_live_fail_message(
                                    trade.symbol,
                                    str(closed_result.get("stage", "close")),
                                    str(closed_result.get("reason", "close failed")),
                                ),
                            )

                    elif price >= trade.tp2:
                        closed_result = await execute_live_close_market_order(trade.id)
                        if closed_result.get("ok"):
                            await send_message(
                                telegram_app,
                                format_live_close_message(
                                    trade.symbol,
                                    "TP2",
                                    float(closed_result.get("exit_price", price)),
                                    float(closed_result.get("result_percent", result_percent)),
                                ),
                            )
                        else:
                            logger.warning(
                                "LIVE CLOSE FAILED %s | trade_id=%s | stage=%s | reason=%s",
                                trade.symbol,
                                trade.id,
                                closed_result.get("stage"),
                                closed_result.get("reason"),
                            )
                            await send_message(
                                telegram_app,
                                format_live_fail_message(
                                    trade.symbol,
                                    str(closed_result.get("stage", "close")),
                                    str(closed_result.get("reason", "close failed")),
                                ),
                            )

                else:
                    result_percent = ((effective_entry_price - price) / effective_entry_price) * 100

                    if abs(result_percent) > 100:
                        logger.warning(
                            "Skip abnormal LIVE SHORT result | trade_id=%s | entry=%s | price=%s | result=%s",
                            trade.id,
                            effective_entry_price,
                            price,
                            result_percent,
                        )
                        continue

                    if not trade.tp1_hit and price <= trade.tp1:
                        marked = mark_live_trade_tp1_hit(trade.id)
                        if marked:
                            activated = activate_live_trade_trailing(trade.id, effective_entry_price)
                            if activated:
                                trade.tp1_hit = marked.tp1_hit
                                trade.trailing_active = activated.trailing_active
                                trade.trailing_sl = activated.trailing_sl

                            await send_message(
                                telegram_app,
                                format_live_tp1_message(
                                    trade.symbol,
                                    price,
                                ),
                            )
                        continue

                    if trade.trailing_active:
                        current_trailing = trade.trailing_sl if trade.trailing_sl is not None else effective_entry_price
                        new_trailing_sl = min(current_trailing, price * 1.005)

                        if new_trailing_sl < current_trailing:
                            updated = update_live_trade_trailing_sl(trade.id, new_trailing_sl)
                            if updated:
                                trade.trailing_sl = updated.trailing_sl
                                await send_message(
                                    telegram_app,
                                    format_live_trailing_message(trade.symbol, updated.trailing_sl),
                                )

                        effective_sl = trade.trailing_sl if trade.trailing_sl is not None else effective_entry_price
                    else:
                        effective_sl = trade.sl

                    if price >= effective_sl:
                        reason = "TSL" if trade.trailing_active else "SL"
                        closed_result = await execute_live_close_market_order(trade.id)
                        if closed_result.get("ok"):
                            await send_message(
                                telegram_app,
                                format_live_close_message(
                                    trade.symbol,
                                    reason,
                                    float(closed_result.get("exit_price", price)),
                                    float(closed_result.get("result_percent", result_percent)),
                                ),
                            )
                        else:
                            logger.warning(
                                "LIVE CLOSE FAILED %s | trade_id=%s | stage=%s | reason=%s",
                                trade.symbol,
                                trade.id,
                                closed_result.get("stage"),
                                closed_result.get("reason"),
                            )
                            await send_message(
                                telegram_app,
                                format_live_fail_message(
                                    trade.symbol,
                                    str(closed_result.get("stage", "close")),
                                    str(closed_result.get("reason", "close failed")),
                                ),
                            )

                    elif price <= trade.tp2:
                        closed_result = await execute_live_close_market_order(trade.id)
                        if closed_result.get("ok"):
                            await send_message(
                                telegram_app,
                                format_live_close_message(
                                    trade.symbol,
                                    "TP2",
                                    float(closed_result.get("exit_price", price)),
                                    float(closed_result.get("result_percent", result_percent)),
                                ),
                            )
                        else:
                            logger.warning(
                                "LIVE CLOSE FAILED %s | trade_id=%s | stage=%s | reason=%s",
                                trade.symbol,
                                trade.id,
                                closed_result.get("stage"),
                                closed_result.get("reason"),
                            )
                            await send_message(
                                telegram_app,
                                format_live_fail_message(
                                    trade.symbol,
                                    str(closed_result.get("stage", "close")),
                                    str(closed_result.get("reason", "close failed")),
                                ),
                            )

            if trades:
                live_error_count = 0

        except Exception as e:
            logger.exception("Live trade loop error: %s", e)

            live_error_count += 1

            if live_error_count >= LIVE_MAX_CONSECUTIVE_ERRORS:
                state = panic_stop()

                await send_message(
                    telegram_app,
                    format_live_error_breaker_message(live_error_count),
                )

                logger.warning(
                    "Live stopped by error breaker | mode=%s",
                    state["trade_mode"],
                )

                live_error_count = 0

        await asyncio.sleep(settings.PAPER_TRADE_CHECK_INTERVAL_SECONDS)


async def performance_loop():
    global telegram_app, performance_loop_last_seen, performance_stale_alert_sent

    while True:
        performance_loop_last_seen = time.time()
        performance_stale_alert_sent = False

        try:
            signals = get_pending_signals()

            for s in signals:
                if s.created_at is None:
                    continue

                now = datetime.now(timezone.utc)
                created_at = s.created_at

                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)

                age = (now - created_at).total_seconds()

                price = await get_symbol_price(s.symbol)
                if not price or s.entry_price <= 0:
                    continue

                if s.side == "SHORT":
                    change = ((s.entry_price - price) / s.entry_price) * 100
                else:
                    change = ((price - s.entry_price) / s.entry_price) * 100

                data = {}

                if s.max_profit is None or change > s.max_profit:
                    data["max_profit"] = change

                if s.max_drawdown is None or change < s.max_drawdown:
                    data["max_drawdown"] = change

                send_msg = None

                if age >= SIGNAL_CHECK_AFTER_5M_SECONDS and s.result_5m is None:
                    data["result_5m"] = change

                    if change > 0.15:
                        status_5m = "win"
                    elif change < -0.15:
                        status_5m = "lose"
                    else:
                        status_5m = "draw"

                    send_msg = format_performance_message(s.symbol, change, status_5m, "5M")

                if age >= SIGNAL_CHECK_AFTER_15M_SECONDS and s.result_15m is None:
                    data["result_15m"] = change

                    if change > 0.15:
                        status_15m = "win"
                    elif change < -0.15:
                        status_15m = "lose"
                    else:
                        status_15m = "draw"

                    send_msg = format_performance_message(s.symbol, change, status_15m, "15M")

                if data:
                    update_performance(s.id, data)

                if send_msg:
                    await send_message(telegram_app, send_msg)

        except Exception as e:
            logger.exception("Performance error: %s", e)

        await asyncio.sleep(settings.PERFORMANCE_CHECK_INTERVAL_SECONDS)


async def heartbeat_loop():
    global telegram_app

    while True:
        try:
            await send_message(telegram_app, format_heartbeat_message())
        except Exception as e:
            logger.exception("Heartbeat error: %s", e)

        await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)


async def watchdog_loop():
    global telegram_app
    global scanner_stale_alert_sent, paper_trade_stale_alert_sent, live_trade_stale_alert_sent, performance_stale_alert_sent

    while True:
        try:
            now = time.time()

            checks = [
                ("scanner_loop", scanner_loop_last_seen, "scanner_stale_alert_sent"),
                ("paper_trade_loop", paper_trade_loop_last_seen, "paper_trade_stale_alert_sent"),
                ("live_trade_loop", live_trade_loop_last_seen, "live_trade_stale_alert_sent"),
                ("performance_loop", performance_loop_last_seen, "performance_stale_alert_sent"),
            ]

            for loop_name, last_seen, flag_name in checks:
                if last_seen <= 0:
                    continue

                age_seconds = now - last_seen
                alert_sent = globals()[flag_name]

                if age_seconds > LOOP_STALE_THRESHOLD_SECONDS:
                    if not alert_sent:
                        await send_message(
                            telegram_app,
                            format_watchdog_alert_message(loop_name, age_seconds),
                        )
                        globals()[flag_name] = True
                else:
                    globals()[flag_name] = False

        except Exception as e:
            logger.exception("Watchdog error: %s", e)

        await asyncio.sleep(WATCHDOG_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global telegram_app, market_task, scanner_task, performance_task, paper_trade_task, live_trade_task, heartbeat_task, watchdog_task
    global scanner_loop_last_seen, paper_trade_loop_last_seen, live_trade_loop_last_seen, performance_loop_last_seen
    global scanner_stale_alert_sent, paper_trade_stale_alert_sent, live_trade_stale_alert_sent, performance_stale_alert_sent

    logger.info("Starting app | env=%s | mode=%s", settings.APP_ENV, settings.APP_MODE)

    Base.metadata.create_all(bind=engine)

    telegram_app = create_bot()

    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()

    now_ts = time.time()
    scanner_loop_last_seen = now_ts
    paper_trade_loop_last_seen = now_ts
    live_trade_loop_last_seen = now_ts
    performance_loop_last_seen = now_ts

    scanner_stale_alert_sent = False
    paper_trade_stale_alert_sent = False
    live_trade_stale_alert_sent = False
    performance_stale_alert_sent = False

    await send_message(
        telegram_app,
        f"🚀 BOT STARTED\n\nEnv: {settings.APP_ENV}\nMode: {settings.APP_MODE}"
    )

    market_task = asyncio.create_task(stream_btc_trades())
    scanner_task = asyncio.create_task(scanner_loop())
    performance_task = asyncio.create_task(performance_loop())
    paper_trade_task = asyncio.create_task(paper_trade_loop())
    live_trade_task = asyncio.create_task(live_trade_loop())
    heartbeat_task = asyncio.create_task(heartbeat_loop())
    watchdog_task = asyncio.create_task(watchdog_loop())

    yield

    logger.info("Shutting down app")

    for task in [market_task, scanner_task, performance_task, paper_trade_task, live_trade_task, heartbeat_task, watchdog_task]:
        if task:
            task.cancel()

    await telegram_app.updater.stop()
    await telegram_app.stop()
    await telegram_app.shutdown()


app = FastAPI(title="Binance Bot", lifespan=lifespan)
app.include_router(health_router)