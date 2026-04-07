import asyncio
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI

from app.api.health import router as health_router
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
from app.services.risk_service import build_risk_plan
from app.services.trade_mode_service import get_trade_mode
from app.services.paper_trade_service import (
    create_paper_trade,
    get_open_paper_trades,
    close_paper_trade,
    partial_close_paper_trade_tp1,
    activate_paper_trade_trailing,
    update_paper_trade_trailing_sl,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

telegram_app = None
market_task = None
scanner_task = None
performance_task = None
paper_trade_task = None

last_alerts = {}

ALERT_COOLDOWN_SECONDS = 900
SCAN_INTERVAL_SECONDS = 30
PERFORMANCE_CHECK_INTERVAL_SECONDS = 60
PAPER_TRADE_CHECK_INTERVAL_SECONDS = 20
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


async def scanner_loop():
    global telegram_app, last_alerts

    while True:
        try:
            logging.info("🔍 Scanner running...")

            results = await scan_market()
            logging.info(f"Found {len(results)} coins")

            now = time.time()
            new_alerts = []

            for coin in results:
                symbol = coin["symbol"]
                score = coin["score"]

                cooldown = ALERT_COOLDOWN_SECONDS
                if score >= 80:
                    cooldown = 300
                elif score >= 60:
                    cooldown = 600

                last_time = last_alerts.get(symbol)

                if last_time is None or now - last_time > cooldown:
                    ai_result = ai_filter_signal(coin)

                    if not ai_result:
                        logging.info(f"AI skipped {symbol}")
                        continue

                    coin["ai"] = ai_result
                    coin["strategy"] = build_strategy(coin)
                    coin["risk"] = build_risk_plan(coin["strategy"])

                    new_alerts.append(coin)
                    last_alerts[symbol] = now

            logging.info(f"Sending {len(new_alerts)} alerts")

            if new_alerts:
                msg = format_market_message(new_alerts)
                await send_message(telegram_app, msg)

                mode = get_trade_mode()

                open_trades = get_open_paper_trades()
                open_symbols = {trade.symbol for trade in open_trades}

                for coin in new_alerts:
                    save_signal(coin)

                    if mode["trade_mode"] == "PAPER" and mode["auto_trade_enabled"]:
                        if coin["symbol"] in open_symbols:
                            logging.info(f"Skip opening duplicate paper trade for {coin['symbol']}")
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

                        open_symbols.add(coin["symbol"])

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

                logging.info(f"Sent {len(new_alerts)} alerts to Telegram + DB")

        except Exception as e:
            logging.error(f"Scanner loop error: {e}")

        await asyncio.sleep(SCAN_INTERVAL_SECONDS)


async def paper_trade_loop():
    global telegram_app

    while True:
        try:
            mode = get_trade_mode()
            if mode["trade_mode"] != "PAPER" or not mode["auto_trade_enabled"]:
                await asyncio.sleep(PAPER_TRADE_CHECK_INTERVAL_SECONDS)
                continue

            trades = get_open_paper_trades()

            for trade in trades:
                price = await get_symbol_price(trade.symbol)
                if not price:
                    continue

                if trade.entry_price <= 0:
                    logging.warning(
                        f"Skip invalid entry_price | trade_id={trade.id} | entry={trade.entry_price}"
                    )
                    continue

                if trade.side == "LONG":
                    result_percent = ((price - trade.entry_price) / trade.entry_price) * 100

                    if abs(result_percent) > 100:
                        logging.warning(
                            f"Skip abnormal LONG result | trade_id={trade.id} "
                            f"| entry={trade.entry_price} | price={price} | result={result_percent}"
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
                        logging.warning(
                            f"Skip abnormal SHORT result | trade_id={trade.id} "
                            f"| entry={trade.entry_price} | price={price} | result={result_percent}"
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
            logging.error(f"Paper trade loop error: {e}")

        await asyncio.sleep(PAPER_TRADE_CHECK_INTERVAL_SECONDS)


async def performance_loop():
    global telegram_app

    while True:
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
            logging.error(f"Performance error: {e}")

        await asyncio.sleep(PERFORMANCE_CHECK_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global telegram_app, market_task, scanner_task, performance_task, paper_trade_task

    Base.metadata.create_all(bind=engine)

    telegram_app = create_bot()

    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()

    market_task = asyncio.create_task(stream_btc_trades())
    scanner_task = asyncio.create_task(scanner_loop())
    performance_task = asyncio.create_task(performance_loop())
    paper_trade_task = asyncio.create_task(paper_trade_loop())

    yield

    if market_task:
        market_task.cancel()

    if scanner_task:
        scanner_task.cancel()

    if performance_task:
        performance_task.cancel()

    if paper_trade_task:
        paper_trade_task.cancel()

    await telegram_app.updater.stop()
    await telegram_app.stop()
    await telegram_app.shutdown()


app = FastAPI(title="Binance Bot", lifespan=lifespan)
app.include_router(health_router)