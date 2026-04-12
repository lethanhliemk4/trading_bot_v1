import time
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update

from app.config import get_settings
from app.services.signal_service import (
    get_latest_signals,
    get_top_signals,
    get_stats,
    save_signal,
    delete_last_signal,
    clear_signals,
)
from app.services.watchlist_service import (
    get_watchlist_symbols,
    add_watchlist_symbol,
    remove_watchlist_symbol,
    clear_watchlist,
)
from app.services.health_service import check_database, check_binance_api
from app.services.ai_filter import ai_filter_signal
from app.services.trade_mode_service import (
    get_trade_mode,
    set_trade_mode,
    panic_stop,
)
from app.services.paper_trade_service import (
    get_open_paper_trades,
    get_all_open_paper_trades,
    get_latest_paper_trades,
    clear_paper_trades,
    create_paper_trade,
    get_paper_trade_stats,
    get_paper_equity,
    export_paper_trades_csv,
    close_paper_trade,
    get_today_realized_pnl,
    is_daily_loss_limit_hit,
)
from app.services.strategy_service import build_strategy
from app.services.risk_service import build_risk_plan
from app.services.market_price_service import get_symbol_price
from app.market.scanner import scan_one
from app.market.rest_client import get_balance
from app.services.live_trade_service import (
    execute_live_market_order,
    get_open_live_trades,
    get_latest_live_trades,
    get_live_trade_stats,
    sync_open_live_trades,
    sync_live_trade_order,
    execute_live_close_market_order,
    get_live_trade_by_id,
)

settings = get_settings()

TOKEN = settings.TELEGRAM_BOT_TOKEN
APP_ENV = settings.APP_ENV
APP_VERSION = settings.APP_VERSION

ALLOWED_IDS = settings.telegram_allowed_user_id_list
LIVE_ALLOWED_IDS = settings.live_allowed_user_id_list

PENDING_CONFIRMATIONS: dict[int, dict] = {}
PENDING_LIVE_CONFIRMATIONS: dict[int, float] = {}
CONFIRM_TTL_SECONDS = 120
LIVE_CONFIRM_TTL_SECONDS = 120


def is_allowed(user_id: int) -> bool:
    return user_id in ALLOWED_IDS


def is_live_allowed(user_id: int) -> bool:
    return user_id in LIVE_ALLOWED_IDS


def set_confirmation(user_id: int, action: str):
    PENDING_CONFIRMATIONS[user_id] = {
        "action": action,
        "created_at": time.time(),
    }


def pop_valid_confirmation(user_id: int, action: str) -> bool:
    item = PENDING_CONFIRMATIONS.get(user_id)
    if not item:
        return False

    if item["action"] != action:
        return False

    if time.time() - item["created_at"] > CONFIRM_TTL_SECONDS:
        PENDING_CONFIRMATIONS.pop(user_id, None)
        return False

    PENDING_CONFIRMATIONS.pop(user_id, None)
    return True


def set_live_confirmation(user_id: int):
    PENDING_LIVE_CONFIRMATIONS[user_id] = time.time()


def pop_valid_live_confirmation(user_id: int) -> bool:
    created_at = PENDING_LIVE_CONFIRMATIONS.get(user_id)
    if not created_at:
        return False

    if time.time() - created_at > LIVE_CONFIRM_TTL_SECONDS:
        PENDING_LIVE_CONFIRMATIONS.pop(user_id, None)
        return False

    PENDING_LIVE_CONFIRMATIONS.pop(user_id, None)
    return True


def format_scan_result(signal: dict) -> str:
    score = signal["score"]
    change = signal["price_change_5m"]
    vol = signal["quote_volume_5m"] / 1_000_000
    spike = signal["volume_spike_ratio"]
    entry = signal["entry_price"]

    if score >= 80:
        tag = "🔥🔥"
    elif score >= 60:
        tag = "🔥"
    else:
        tag = "📈"

    return (
        "🔍 SCAN RESULT\n\n"
        f"{tag} {signal['symbol']}\n"
        f"Score: {score:.0f}\n"
        f"5m Change: {change:+.2f}%\n"
        f"Volume: {vol:.2f}M\n"
        f"Spike: x{spike:.2f}\n"
        f"Entry: {entry:.6f}"
    )


def format_alert_message(signal: dict) -> str:
    score = signal["score"]
    change = signal["price_change_5m"]
    vol = signal["quote_volume_5m"] / 1_000_000
    spike = signal["volume_spike_ratio"]

    if score >= 80:
        tag = "🔥🔥"
    elif score >= 60:
        tag = "🔥"
    else:
        tag = "📈"

    lines = [
        "🚀 FORCE ALERT",
        "",
        f"{tag} {signal['symbol']} | Score: {score:.0f}",
        f"   5m: {change:+.2f}% | Vol: {vol:.2f}M | Spike: x{spike:.2f}",
    ]

    ai = signal.get("ai")
    if ai:
        lines.append(f"   🤖 AI: {ai['confidence']:.0f}% - {ai['reason']}")

    strategy = signal.get("strategy")
    if strategy:
        lines.append(f"   🎯 Entry: {strategy['entry']:.6f}")
        lines.append(f"   🛑 SL: {strategy['sl']:.6f}")
        lines.append(f"   🎯 TP1: {strategy['tp1']:.6f}")
        lines.append(f"   🚀 TP2: {strategy['tp2']:.6f}")
        lines.append(f"   ⚖️ RR: 1:{strategy['rr']:.2f}")

    risk = signal.get("risk")
    if risk:
        lines.append(f"   💰 Capital: {risk['capital']:.2f} USDT")
        lines.append(f"   ⚠️ Risk: {risk['risk_percent']:.2f}% = {risk['risk_amount']:.2f} USDT")
        lines.append(f"   📦 Position Size: {risk['position_size']:.6f}")
        lines.append(f"   💵 Notional: {risk['notional']:.2f} USDT")

    return "\n".join(lines)


def format_scanall_results(results: list[dict]) -> str:
    lines = ["📡 SCANALL RESULT", ""]

    for signal in results:
        score = signal["score"]
        change = signal["price_change_5m"]

        if score >= 80:
            tag = "🔥🔥"
        elif score >= 60:
            tag = "🔥"
        else:
            tag = "📈"

        lines.append(f"{tag} {signal['symbol']} | Score: {score:.0f} | {change:+.2f}%")

    return "\n".join(lines).strip()


def format_ai_test_result(symbol: str, signal: dict, ai_result: dict | None) -> str:
    score = signal["score"]
    change = signal["price_change_5m"]
    vol = signal["quote_volume_5m"] / 1_000_000
    spike = signal["volume_spike_ratio"]

    lines = [
        "🤖 AI TEST RESULT",
        "",
        f"Symbol: {symbol}",
        f"Score: {score:.0f}",
        f"5m Change: {change:+.2f}%",
        f"Volume: {vol:.2f}M",
        f"Spike: x{spike:.2f}",
        "",
    ]

    if ai_result:
        lines.extend([
            f"Decision: {ai_result['decision']}",
            f"Confidence: {ai_result['confidence']:.0f}%",
            f"Reason: {ai_result['reason']}",
        ])
    else:
        lines.append("Decision: SKIP or AI rejected signal")

    return "\n".join(lines)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return
    await update.message.reply_text("🚀 Bot is running")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    mode_state = get_trade_mode()

    await update.message.reply_text(
        "✅ Bot status: RUNNING\n"
        f"Trade mode: {mode_state['trade_mode']}\n"
        f"Auto trade: {'ON' if mode_state['auto_trade_enabled'] else 'OFF'}\n"
        f"App env: {APP_ENV}\n"
        f"App mode: {settings.APP_MODE}\n"
        f"KILL_SWITCH: {settings.KILL_SWITCH}"
    )


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return
    await update.message.reply_text("🏓 Pong! Bot is alive")


async def version(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    msg = (
        "📦 BOT VERSION\n\n"
        f"Version: {APP_VERSION}\n"
        f"Environment: {APP_ENV}\n"
        f"Mode: {settings.APP_MODE}"
    )
    await update.message.reply_text(msg)


async def healthcheck(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    db_ok = check_database()
    binance_ok = await check_binance_api()

    msg = (
        "🩺 HEALTHCHECK\n\n"
        "Telegram: OK\n"
        f"Database: {'OK' if db_ok else 'FAIL'}\n"
        f"Binance API: {'OK' if binance_ok else 'FAIL'}"
    )

    await update.message.reply_text(msg)


async def mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    if not context.args:
        current = get_trade_mode()
        await update.message.reply_text(
            "Usage: /mode off|paper|live\n\n"
            f"Current mode: {current['trade_mode']}\n"
            f"Auto trade: {'ON' if current['auto_trade_enabled'] else 'OFF'}"
        )
        return

    try:
        new_mode = context.args[0].upper().strip()

        if new_mode == "LIVE":
            set_live_confirmation(user_id)
            await update.message.reply_text(
                "⚠️ LIVE mode is dangerous\n\n"
                "This can enable real-money trading logic later.\n\n"
                "Run within 2 minutes:\n/confirm_live"
            )
            return

        state = set_trade_mode(new_mode)
        await update.message.reply_text(
            "✅ Trade mode updated\n\n"
            f"Mode: {state['trade_mode']}\n"
            f"Auto trade: {'ON' if state['auto_trade_enabled'] else 'OFF'}"
        )
    except ValueError as e:
        await update.message.reply_text(f"❌ {str(e)}")


async def confirm_live(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    if APP_ENV.lower() != "prod":
        await update.message.reply_text(
            "🚫 LIVE MODE BLOCKED\n\n"
            f"Current ENV: {APP_ENV}\n"
            "LIVE mode is only allowed in production."
        )
        return

    if not is_live_allowed(user_id):
        await update.message.reply_text(
            "🚫 LIVE MODE BLOCKED\n\n"
            "Your Telegram account is not allowed to enable LIVE mode."
        )
        return

    if not pop_valid_live_confirmation(user_id):
        await update.message.reply_text("❌ No valid LIVE confirmation or confirmation expired")
        return

    state = set_trade_mode("LIVE")

    await update.message.reply_text(
        "🚨 LIVE MODE ENABLED\n\n"
        f"Mode: {state['trade_mode']}\n"
        f"Auto trade: {'ON' if state['auto_trade_enabled'] else 'OFF'}\n\n"
        "⚠️ REAL TRADING LOGIC MAY BE ACTIVE"
    )


async def panic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    state = panic_stop()
    PENDING_LIVE_CONFIRMATIONS.pop(user_id, None)

    await update.message.reply_text(
        "🛑 PANIC MODE ACTIVATED\n\n"
        f"Mode: {state['trade_mode']}\n"
        f"Auto trade: {'ON' if state['auto_trade_enabled'] else 'OFF'}"
    )


async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    if not context.args:
        await update.message.reply_text("Usage: /confirm paper_reset|paper_clear|clear_signals")
        return

    action = context.args[0].strip().lower()

    if not pop_valid_confirmation(user_id, action):
        await update.message.reply_text("❌ No valid pending confirmation or confirmation expired")
        return

    if action == "paper_reset":
        paper_count = clear_paper_trades()
        signal_count = clear_signals()
        await update.message.reply_text(
            "♻️ PAPER RESET DONE\n\n"
            f"Paper trades cleared: {paper_count}\n"
            f"Signals cleared: {signal_count}"
        )
        return

    if action == "paper_clear":
        count = clear_paper_trades()
        await update.message.reply_text(f"🧹 Cleared {count} paper trades")
        return

    if action == "clear_signals":
        count = clear_signals()
        await update.message.reply_text(f"🧹 Cleared {count} signals")
        return

    await update.message.reply_text("❌ Unsupported confirmation action")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    msg = (
        "🤖 AVAILABLE COMMANDS\n\n"
        "/start - Check bot is alive\n"
        "/status - Show bot status\n"
        "/ping - Quick bot ping\n"
        "/version - Show app version\n"
        "/healthcheck - Check Telegram + DB + Binance\n"
        "/help - Show all commands\n"
        "/balance - Show USDT balance\n\n"
        "/mode off|paper|live - Set trade mode\n"
        "/confirm_live - Confirm LIVE mode\n"
        "/panic - Turn auto trade off immediately\n"
        "/confirm <action> - Confirm dangerous action\n"
        "/live_test BTCUSDT - Execute one manual live test trade\n"
        "/live_open - Show open live trades\n"
        "/live_history - Show latest live trades\n"
        "/live_stats - Show live trade stats\n"
        "/live_sync - Sync open live trades from Binance\n"
        "/live_sync_one 123 - Sync one live trade by ID\n"
        "/live_close_test 123 - Close one live trade by ID\n"
        "/live_detail 123 - Show one live trade detail\n\n"
        "/history - Show latest signals\n"
        "/top - Show top scored signals\n"
        "/stats - Show performance stats\n"
        "/delete_last_signal - Delete newest signal\n"
        "/clear_signals - Request clear all signals\n\n"
        "/paper_open - Show open paper trades\n"
        "/paper_history - Show paper trade history\n"
        "/paper_clear - Request clear all paper trades\n"
        "/paper_stats - Show paper trade stats\n"
        "/paper_equity - Show paper equity summary\n"
        "/paper_today - Show today realized PnL\n"
        "/paper_export - Export paper trades CSV\n"
        "/paper_close_all - Close all open paper trades\n"
        "/paper_reset - Request reset paper trades and signals\n\n"
        "/watchlist - Show current watchlist\n"
        "/watchadd BTCUSDT - Add symbol to watchlist\n"
        "/watchremove BTCUSDT - Remove symbol from watchlist\n"
        "/watchclear - Clear all watchlist symbols\n\n"
        "/scan BTCUSDT - Scan one symbol now\n"
        "/scanall - Scan all symbols in watchlist now\n"
        "/aitest BTCUSDT - Test Gemini on one symbol\n"
        "/forcealert BTCUSDT - Force send and save a test alert"
    )

    await update.message.reply_text(msg)


async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    signals = get_latest_signals(10)
    if not signals:
        await update.message.reply_text("No signals yet")
        return

    msg = "📊 LAST SIGNALS\n\n"
    for s in signals:
        msg += (
            f"{s.symbol} | Score: {s.score:.0f} | "
            f"{s.price_change_5m:+.2f}% | Status: {s.status}\n"
        )

    await update.message.reply_text(msg)


async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    signals = get_top_signals(10)
    if not signals:
        await update.message.reply_text("No signals yet")
        return

    msg = "🏆 TOP SIGNALS\n\n"
    for s in signals:
        if s.score >= 80:
            tag = "🔥🔥"
        elif s.score >= 60:
            tag = "🔥"
        else:
            tag = "📈"

        msg += f"{tag} {s.symbol} | Score: {s.score:.0f} | {s.price_change_5m:+.2f}%\n"

    await update.message.reply_text(msg)


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    s = get_stats()
    s5 = s["five_min"]
    s15 = s["fifteen_min"]

    msg = (
        "📊 PERFORMANCE\n\n"
        "⏱ 5M\n"
        f"Total: {s5['total']}\n"
        f"Wins: {s5['wins']} | Loses: {s5['loses']} | Draws: {s5['draws']}\n"
        f"Winrate: {s5['winrate']:.2f}%\n"
        f"Avg: {s5['avg']:+.2f}%\n\n"
        "⏱ 15M\n"
        f"Total: {s15['total']}\n"
        f"Wins: {s15['wins']} | Loses: {s15['loses']} | Draws: {s15['draws']}\n"
        f"Winrate: {s15['winrate']:.2f}%\n"
        f"Avg: {s15['avg']:+.2f}%\n\n"
        "📈 OVERALL\n"
        f"Completed Signals: {s['done_total']}\n"
        f"Avg Max Profit: {s['avg_max_profit']:+.2f}%\n"
        f"Avg Max Drawdown: {s['avg_max_drawdown']:+.2f}%"
    )

    await update.message.reply_text(msg)


async def delete_last_signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    symbol = delete_last_signal()
    if not symbol:
        await update.message.reply_text("No signals to delete")
        return

    await update.message.reply_text(f"🗑 Deleted latest signal: {symbol}")


async def clear_signals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    set_confirmation(user_id, "clear_signals")
    await update.message.reply_text(
        "⚠️ Confirm clear all signals\n\n"
        "Run:\n/confirm clear_signals"
    )


async def paper_open(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    trades = get_open_paper_trades()

    if not trades:
        await update.message.reply_text("📭 No open paper trades")
        return

    msg = "🧪 OPEN PAPER TRADES\n\n"
    for t in trades:
        msg += (
            f"{t.symbol} | {t.side}\n"
            f"Entry: {t.entry_price:.4f} | SL: {t.sl:.4f} | TP2: {t.tp2:.4f}\n\n"
        )

    await update.message.reply_text(msg)


async def paper_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    trades = get_latest_paper_trades()

    if not trades:
        await update.message.reply_text("📭 No paper trades yet")
        return

    msg = "📊 PAPER TRADE HISTORY\n\n"

    for t in trades:
        status_icon = "🟢" if t.status == "OPEN" else "🔴"
        msg += f"{status_icon} {t.symbol} | {t.side} | {t.status}\n"

        if t.result_percent is not None:
            msg += f"Result: {t.result_percent:+.2f}%\n"

        msg += "\n"

    await update.message.reply_text(msg)


async def paper_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    set_confirmation(user_id, "paper_clear")
    await update.message.reply_text(
        "⚠️ Confirm clear all paper trades\n\n"
        "Run:\n/confirm paper_clear"
    )


async def paper_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    s = get_paper_trade_stats()

    msg = (
        "📊 PAPER STATS\n\n"
        f"Total: {s['total']}\n"
        f"Open: {s['open']}\n"
        f"Closed: {s['closed']}\n\n"
        f"Wins: {s['wins']}\n"
        f"Loses: {s['loses']}\n"
        f"Draws: {s['draws']}\n"
        f"Winrate: {s['winrate']:.2f}%\n\n"
        f"Avg Result: {s['avg_result']:+.2f}%\n"
        f"Best: {s['best_result']:+.2f}%\n"
        f"Worst: {s['worst_result']:+.2f}%"
    )

    await update.message.reply_text(msg)


async def paper_equity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    e = get_paper_equity()

    msg = (
        "📈 PAPER EQUITY\n\n"
        f"Start Capital: {e['start_capital']:.2f} USDT\n"
        f"Realized PnL: {e['realized_pnl']:+.2f} USDT\n"
        f"Current Equity: {e['current_equity']:.2f} USDT\n\n"
        f"Closed Trades: {e['closed_trades']}\n"
        f"Avg PnL / Trade: {e['avg_pnl_per_trade']:+.2f} USDT"
    )

    await update.message.reply_text(msg)


async def paper_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    pnl = get_today_realized_pnl()
    limit_hit, _ = is_daily_loss_limit_hit()

    msg = (
        "📅 PAPER TODAY\n\n"
        f"Realized PnL: {pnl:+.2f} USDT\n"
        f"Daily Loss Limit: -{abs(settings.DAILY_LOSS_LIMIT_USDT):.2f} USDT\n"
    )

    if limit_hit:
        msg += "\n🛑 Circuit Breaker: TRIGGERED"
    else:
        msg += "\n✅ Circuit Breaker: OK"

    await update.message.reply_text(msg)


async def paper_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    filepath = export_paper_trades_csv()

    if not filepath:
        await update.message.reply_text("📭 No paper trades to export")
        return

    with open(filepath, "rb") as f:
        await update.message.reply_document(document=f)


async def paper_close_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    trades = get_all_open_paper_trades()
    if not trades:
        await update.message.reply_text("📭 No open paper trades to close")
        return

    closed_count = 0
    skipped_count = 0

    for trade in trades:
        price = await get_symbol_price(trade.symbol)
        if not price or trade.entry_price <= 0:
            skipped_count += 1
            continue

        if trade.side == "LONG":
            result_percent = ((price - trade.entry_price) / trade.entry_price) * 100
        else:
            result_percent = ((trade.entry_price - price) / trade.entry_price) * 100

        if abs(result_percent) > 100:
            skipped_count += 1
            continue

        closed = close_paper_trade(trade.id, price, result_percent, "MANUAL_CLOSE")
        if closed:
            closed_count += 1

    await update.message.reply_text(
        "🧹 PAPER CLOSE ALL DONE\n\n"
        f"Closed: {closed_count}\n"
        f"Skipped: {skipped_count}"
    )


async def paper_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    set_confirmation(user_id, "paper_reset")
    await update.message.reply_text(
        "⚠️ Confirm paper reset\n\n"
        "This will clear all paper trades and signals.\n\n"
        "Run:\n/confirm paper_reset"
    )


async def watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    symbols = get_watchlist_symbols()
    if not symbols:
        await update.message.reply_text("📌 Watchlist is empty")
        return

    msg = "📌 WATCHLIST\n\n" + "\n".join(symbols)
    await update.message.reply_text(msg)


async def watchadd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    if not context.args:
        await update.message.reply_text("Usage: /watchadd BTCUSDT")
        return

    symbol = context.args[0].upper().strip()
    ok = add_watchlist_symbol(symbol)

    if ok:
        await update.message.reply_text(f"✅ Added {symbol} to watchlist")
    else:
        await update.message.reply_text(f"⚠️ {symbol} already exists")


async def watchremove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    if not context.args:
        await update.message.reply_text("Usage: /watchremove BTCUSDT")
        return

    symbol = context.args[0].upper().strip()
    ok = remove_watchlist_symbol(symbol)

    if ok:
        await update.message.reply_text(f"🗑 Removed {symbol} from watchlist")
    else:
        await update.message.reply_text(f"⚠️ {symbol} not found")


async def watchclear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    deleted = clear_watchlist()

    if deleted == 0:
        await update.message.reply_text("📌 Watchlist is already empty")
        return

    await update.message.reply_text(f"🧹 Cleared watchlist ({deleted} symbols)")


async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    if not context.args:
        await update.message.reply_text("Usage: /scan BTCUSDT")
        return

    symbol = context.args[0].upper().strip()
    await update.message.reply_text(f"🔍 Scanning {symbol}...")

    result = await scan_one(symbol)

    if not result:
        await update.message.reply_text(f"{symbol}: no signal right now")
        return

    await update.message.reply_text(format_scan_result(result))


async def scanall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    symbols = get_watchlist_symbols()
    if not symbols:
        await update.message.reply_text("📌 Watchlist is empty. Add coins first with /watchadd BTCUSDT")
        return

    await update.message.reply_text(f"📡 Scanning watchlist... ({len(symbols)} coins)")

    results = []
    for symbol in symbols:
        result = await scan_one(symbol)
        if result:
            results.append(result)

    if not results:
        await update.message.reply_text("No signals found in watchlist right now")
        return

    results.sort(key=lambda x: x["score"], reverse=True)
    await update.message.reply_text(format_scanall_results(results[:10]))


async def aitest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    if not context.args:
        await update.message.reply_text("Usage: /aitest BTCUSDT")
        return

    symbol = context.args[0].upper().strip()
    await update.message.reply_text(f"🤖 AI testing {symbol}...")

    result = await scan_one(symbol)

    if not result:
        await update.message.reply_text(f"{symbol}: no base signal to send to AI right now")
        return

    ai_result = ai_filter_signal(result)
    msg = format_ai_test_result(symbol, result, ai_result)
    await update.message.reply_text(msg)


async def forcealert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    if not context.args:
        await update.message.reply_text("Usage: /forcealert BTCUSDT")
        return

    symbol = context.args[0].upper().strip()
    await update.message.reply_text(f"🚨 Forcing alert for {symbol}...")

    result = await scan_one(symbol)

    if not result:
        price = await get_symbol_price(symbol)

        if not price:
            await update.message.reply_text(f"❌ Cannot fetch price for {symbol}")
            return

        result = {
            "symbol": symbol,
            "side": "LONG",
            "score": 50,
            "price_change_5m": 0.30,
            "quote_volume_5m": 200000.0,
            "volume_spike_ratio": 1.50,
            "entry_price": price,
            "atr": price * 0.005,
        }

    ai_result = ai_filter_signal(result)
    if ai_result:
        result["ai"] = ai_result

    result["strategy"] = build_strategy(result)
    result["risk"] = build_risk_plan(result["strategy"])

    if not result["risk"]:
        await update.message.reply_text("⚠️ Risk rejected this setup")
        return

    await update.message.reply_text(format_alert_message(result))
    save_signal(result)

    mode_state = get_trade_mode()
    if mode_state["trade_mode"] == "PAPER" and mode_state["auto_trade_enabled"]:
        open_trades = get_open_paper_trades()
        symbols_open = {t.symbol for t in open_trades}

        if result["symbol"] in symbols_open:
            await update.message.reply_text(
                f"⚠️ Trade already open for {result['symbol']}, skipping"
            )
        else:
            trade = create_paper_trade({
                "symbol": result["symbol"],
                "side": result["strategy"]["side"],
                "entry_price": result["strategy"]["entry"],
                "sl": result["strategy"]["sl"],
                "tp1": result["strategy"]["tp1"],
                "tp2": result["strategy"]["tp2"],
                "rr": result["strategy"]["rr"],
                "risk_amount": result["risk"]["risk_amount"],
                "position_size": result["risk"]["position_size"],
                "notional": result["risk"]["notional"],
            })

            if not trade:
                await update.message.reply_text("⚠️ Paper trade rejected (risk or duplicate)")
                return

            await update.message.reply_text(
                f"🧪 PAPER TRADE OPENED\n\n"
                f"{trade.symbol} | {trade.side}\n"
                f"Entry: {trade.entry_price:.6f}\n"
                f"SL: {trade.sl:.6f}\n"
                f"TP2: {trade.tp2:.6f}"
            )

    await update.message.reply_text(f"✅ Forced alert saved to DB for {symbol}")


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    try:
        usdt = await get_balance("USDT")

        await update.message.reply_text(
            "💰 ACCOUNT BALANCE\n\n"
            f"USDT: {usdt:.4f}\n"
            f"Env: {'TESTNET' if settings.BINANCE_USE_TESTNET else 'MAINNET'}"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def live_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    if not is_live_allowed(user_id):
        await update.message.reply_text("❌ Not allowed for LIVE testing")
        return

    if not context.args:
        await update.message.reply_text("Usage: /live_test BTCUSDT")
        return

    symbol = context.args[0].upper().strip()

    await update.message.reply_text(f"🧪 LIVE TEST {symbol}...")

    result = await scan_one(symbol)

    if not result:
        await update.message.reply_text("❌ No signal found")
        return

    result["strategy"] = build_strategy(result)
    result["risk"] = build_risk_plan(result["strategy"])

    if not result["risk"]:
        await update.message.reply_text("❌ Risk rejected")
        return

    res = await execute_live_market_order(
        result["strategy"],
        result["risk"],
    )

    if not res["ok"]:
        await update.message.reply_text(
            "❌ LIVE FAILED\n\n"
            f"Stage: {res.get('stage')}\n"
            f"Reason: {res.get('reason')}\n"
            f"Symbol: {res.get('symbol', symbol)}"
        )
        return

    await update.message.reply_text(
        "🚨 LIVE TEST SUCCESS\n\n"
        f"Symbol: {symbol}\n"
        f"Stage: {res.get('stage')}\n"
        f"Qty: {res.get('qty')}\n"
        f"Qty Str: {res.get('qty_str')}\n"
        f"Env: {'TESTNET' if res.get('binance_use_testnet') else 'MAINNET'}"
    )


async def live_open(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    trades = get_open_live_trades()

    if not trades:
        await update.message.reply_text("📭 No open live trades")
        return

    msg = "🚨 OPEN LIVE TRADES\n\n"
    for t in trades:
        msg += (
            f"{t.symbol} | {t.side} | {t.environment}\n"
            f"Entry: {t.entry_price:.6f}\n"
            f"Req Qty: {t.requested_qty:.8f} | Exec Qty: {t.executed_qty:.8f}\n"
            f"SL: {t.sl:.6f} | TP2: {t.tp2:.6f}\n"
            f"Status: {t.status}\n\n"
        )

    await update.message.reply_text(msg)


async def live_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    trades = get_latest_live_trades()

    if not trades:
        await update.message.reply_text("📭 No live trades yet")
        return

    msg = "📊 LIVE TRADE HISTORY\n\n"
    for t in trades:
        status_icon = "🟢" if t.status == "OPEN" else "🔴"
        msg += f"{status_icon} {t.symbol} | {t.side} | {t.status}\n"
        msg += f"Env: {t.environment} | Req: {t.requested_qty:.8f} | Exec: {t.executed_qty:.8f}\n"
        if t.result_percent is not None:
            msg += f"Result: {t.result_percent:+.2f}%\n"
        if t.fail_reason:
            msg += f"Fail: {t.fail_reason}\n"
        msg += "\n"

    await update.message.reply_text(msg)


async def live_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    s = get_live_trade_stats()

    msg = (
        "📈 LIVE STATS\n\n"
        f"Total: {s['total']}\n"
        f"Open: {s['open']}\n"
        f"Closed: {s['closed']}\n"
        f"Failed: {s['failed']}\n\n"
        f"Wins: {s['wins']}\n"
        f"Loses: {s['loses']}\n"
        f"Draws: {s['draws']}\n"
        f"Winrate: {s['winrate']:.2f}%\n\n"
        f"Avg Result: {s['avg_result']:+.2f}\n"
        f"Best: {s['best_result']:+.2f}\n"
        f"Worst: {s['worst_result']:+.2f}\n"
        f"TP1 Hits: {s['tp1_hits']}"
    )

    await update.message.reply_text(msg)


async def live_sync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    if not is_live_allowed(user_id):
        await update.message.reply_text("❌ Not allowed for LIVE sync")
        return

    await update.message.reply_text("🔄 Syncing open live trades from Binance...")

    try:
        synced_ids = await sync_open_live_trades()
        count = len(synced_ids or [])
        await update.message.reply_text(
            "✅ LIVE SYNC DONE\n\n"
            f"Updated trades: {count}\n"
            f"Env: {'TESTNET' if settings.BINANCE_USE_TESTNET else 'MAINNET'}"
        )
    except Exception as e:
        await update.message.reply_text(
            "❌ LIVE SYNC FAILED\n\n"
            f"Reason: {str(e)}"
        )


async def live_sync_one(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    if not is_live_allowed(user_id):
        await update.message.reply_text("❌ Not allowed for LIVE sync")
        return

    if not context.args:
        await update.message.reply_text("Usage: /live_sync_one 123")
        return

    try:
        trade_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ trade_id must be an integer")
        return

    await update.message.reply_text(f"🔄 Syncing live trade #{trade_id}...")

    try:
        trade = await sync_live_trade_order(trade_id)
        if not trade:
            await update.message.reply_text(f"❌ Live trade #{trade_id} not found")
            return

        await update.message.reply_text(
            "✅ LIVE SYNC ONE DONE\n\n"
            f"Trade ID: {trade.id}\n"
            f"Symbol: {trade.symbol}\n"
            f"Status: {trade.status}\n"
            f"Entry Order Status: {trade.entry_order_status}\n"
            f"Requested Qty: {trade.requested_qty:.8f}\n"
            f"Executed Qty: {trade.executed_qty:.8f}\n"
            f"Avg Fill Price: {(trade.avg_fill_price or 0.0):.8f}\n"
            f"Env: {trade.environment}"
        )
    except Exception as e:
        await update.message.reply_text(
            "❌ LIVE SYNC ONE FAILED\n\n"
            f"Reason: {str(e)}"
        )


async def live_close_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    if not is_live_allowed(user_id):
        await update.message.reply_text("❌ Not allowed for LIVE close")
        return

    if not context.args:
        await update.message.reply_text("Usage: /live_close_test 123")
        return

    try:
        trade_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ trade_id must be an integer")
        return

    await update.message.reply_text(f"🚨 Closing live trade #{trade_id}...")

    try:
        result = await execute_live_close_market_order(trade_id)

        if not result.get("ok"):
            await update.message.reply_text(
                "❌ LIVE CLOSE FAILED\n\n"
                f"Trade ID: {trade_id}\n"
                f"Stage: {result.get('stage')}\n"
                f"Reason: {result.get('reason')}\n"
                f"Symbol: {result.get('symbol', '-')}"
            )
            return

        await update.message.reply_text(
            "✅ LIVE CLOSE SUCCESS\n\n"
            f"Trade ID: {result.get('trade_id')}\n"
            f"Symbol: {result.get('symbol')}\n"
            f"Exit Side: {result.get('exit_side')}\n"
            f"Qty: {result.get('qty')}\n"
            f"Qty Str: {result.get('qty_str')}\n"
            f"Executed Qty: {result.get('executed_qty')}\n"
            f"Exit Price: {result.get('exit_price'):.8f}\n"
            f"Result: {result.get('result_percent'):+.2f}%\n"
            f"PnL: {result.get('realized_pnl'):+.8f}\n"
            f"Env: {'TESTNET' if result.get('binance_use_testnet') else 'MAINNET'}"
        )
    except Exception as e:
        await update.message.reply_text(
            "❌ LIVE CLOSE FAILED\n\n"
            f"Reason: {str(e)}"
        )


async def live_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_allowed(user_id):
        await update.message.reply_text("❌ Unauthorized")
        return

    if not context.args:
        await update.message.reply_text("Usage: /live_detail 123")
        return

    try:
        trade_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ trade_id must be an integer")
        return

    trade = get_live_trade_by_id(trade_id)
    if not trade:
        await update.message.reply_text(f"❌ Live trade #{trade_id} not found")
        return

    msg = (
        "📌 LIVE TRADE DETAIL\n\n"
        f"Trade ID: {trade.id}\n"
        f"Symbol: {trade.symbol}\n"
        f"Side: {trade.side}\n"
        f"Status: {trade.status}\n"
        f"Environment: {trade.environment}\n"
        f"Exchange: {trade.exchange}\n\n"
        f"Entry Price: {trade.entry_price:.8f}\n"
        f"Avg Fill Price: {(trade.avg_fill_price or 0.0):.8f}\n"
        f"SL: {trade.sl:.8f}\n"
        f"TP1: {trade.tp1:.8f}\n"
        f"TP2: {trade.tp2:.8f}\n"
        f"RR: {trade.rr:.4f}\n\n"
        f"Risk Amount: {trade.risk_amount:.8f}\n"
        f"Position Size: {trade.position_size:.8f}\n"
        f"Notional: {trade.notional:.8f}\n"
        f"Requested Qty: {trade.requested_qty:.8f}\n"
        f"Executed Qty: {trade.executed_qty:.8f}\n"
        f"Remaining Qty: {trade.remaining_qty:.8f}\n\n"
        f"Entry Order ID: {trade.entry_order_id}\n"
        f"Entry Client Order ID: {trade.entry_client_order_id}\n"
        f"Entry Order Status: {trade.entry_order_status}\n"
        f"Exit Order ID: {trade.exit_order_id}\n"
        f"Exit Order Status: {trade.exit_order_status}\n\n"
        f"TP1 Hit: {trade.tp1_hit}\n"
        f"Trailing Active: {trade.trailing_active}\n"
        f"Trailing SL: {(trade.trailing_sl or 0.0):.8f}\n"
        f"Realized PnL: {(trade.realized_pnl or 0.0):+.8f}\n"
        f"Result %: {(trade.result_percent or 0.0):+.2f}%\n"
        f"Exit Price: {(trade.exit_price or 0.0):.8f}\n"
        f"Close Reason: {trade.close_reason}\n"
        f"Fail Reason: {trade.fail_reason}\n\n"
        f"Created At: {trade.created_at}\n"
        f"Opened At: {trade.opened_at}\n"
        f"Closed At: {trade.closed_at}\n"
        f"Last Synced At: {trade.last_synced_at}"
    )

    await update.message.reply_text(msg)


async def send_message(app, text: str):
    for user_id in ALLOWED_IDS:
        await app.bot.send_message(chat_id=user_id, text=text)


def create_bot():
    if not TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is missing")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("version", version))
    app.add_handler(CommandHandler("healthcheck", healthcheck))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("mode", mode))
    app.add_handler(CommandHandler("confirm_live", confirm_live))
    app.add_handler(CommandHandler("panic", panic))
    app.add_handler(CommandHandler("confirm", confirm))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("delete_last_signal", delete_last_signal_command))
    app.add_handler(CommandHandler("clear_signals", clear_signals_command))
    app.add_handler(CommandHandler("paper_open", paper_open))
    app.add_handler(CommandHandler("paper_history", paper_history))
    app.add_handler(CommandHandler("paper_clear", paper_clear))
    app.add_handler(CommandHandler("paper_stats", paper_stats))
    app.add_handler(CommandHandler("paper_equity", paper_equity))
    app.add_handler(CommandHandler("paper_today", paper_today))
    app.add_handler(CommandHandler("paper_export", paper_export))
    app.add_handler(CommandHandler("paper_close_all", paper_close_all))
    app.add_handler(CommandHandler("paper_reset", paper_reset))
    app.add_handler(CommandHandler("watchlist", watchlist))
    app.add_handler(CommandHandler("watchadd", watchadd))
    app.add_handler(CommandHandler("watchremove", watchremove))
    app.add_handler(CommandHandler("watchclear", watchclear))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("scanall", scanall))
    app.add_handler(CommandHandler("aitest", aitest))
    app.add_handler(CommandHandler("forcealert", forcealert))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("live_test", live_test))
    app.add_handler(CommandHandler("live_open", live_open))
    app.add_handler(CommandHandler("live_history", live_history))
    app.add_handler(CommandHandler("live_stats", live_stats))
    app.add_handler(CommandHandler("live_sync", live_sync))
    app.add_handler(CommandHandler("live_sync_one", live_sync_one))
    app.add_handler(CommandHandler("live_close_test", live_close_test))
    app.add_handler(CommandHandler("live_detail", live_detail))

    return app