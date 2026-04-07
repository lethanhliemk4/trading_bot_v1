from app.config import get_settings
from app.services.paper_trade_service import (
    get_open_paper_trades,
    get_today_realized_pnl,
    is_daily_loss_limit_hit,
)

settings = get_settings()


def get_capital() -> float:
    return float(settings.RISK_CAPITAL_USDT)


def get_risk_percent() -> float:
    return float(settings.RISK_PER_TRADE_PERCENT)


def validate_strategy(strategy: dict) -> tuple[bool, str | None]:
    try:
        symbol = str(strategy["symbol"]).upper().strip()
        side = str(strategy["side"]).upper().strip()
        entry = float(strategy["entry"])
        sl = float(strategy["sl"])
        tp1 = float(strategy["tp1"])
        tp2 = float(strategy["tp2"])
        rr = float(strategy.get("rr", 0))
    except Exception:
        return False, "Invalid strategy format"

    if not symbol:
        return False, "Missing symbol"

    if side not in {"LONG", "SHORT"}:
        return False, "Invalid side"

    if entry <= 0:
        return False, "Invalid entry price"

    if sl <= 0 or tp1 <= 0 or tp2 <= 0:
        return False, "Invalid SL/TP values"

    if rr <= 0:
        return False, "Invalid RR"

    if side == "LONG":
        if sl >= entry:
            return False, "SL must be below entry for LONG"
        if tp1 <= entry or tp2 <= entry:
            return False, "TP1/TP2 must be above entry for LONG"
        if tp2 <= tp1:
            return False, "TP2 must be above TP1 for LONG"

    if side == "SHORT":
        if sl <= entry:
            return False, "SL must be above entry for SHORT"
        if tp1 >= entry or tp2 >= entry:
            return False, "TP1/TP2 must be below entry for SHORT"
        if tp2 >= tp1:
            return False, "TP2 must be below TP1 for SHORT"

    return True, None


def validate_risk_limits(symbol: str, notional: float, risk_amount: float) -> tuple[bool, str | None]:
    if settings.KILL_SWITCH:
        return False, "KILL_SWITCH active"

    if risk_amount <= 0:
        return False, "Invalid risk amount"

    limit_hit, today_pnl = is_daily_loss_limit_hit()
    if limit_hit:
        return False, f"Daily loss limit hit ({today_pnl:+.2f})"

    open_trades = get_open_paper_trades(limit=max(settings.MAX_OPEN_TRADES, 100))

    if len(open_trades) >= settings.MAX_OPEN_TRADES:
        return False, "Max open trades reached"

    for trade in open_trades:
        if trade.symbol.upper() == symbol.upper():
            return False, f"Trade already open for {symbol}"

    if notional <= 0:
        return False, "Invalid notional"

    if notional > settings.MAX_NOTIONAL_PER_TRADE:
        return False, f"Notional too high ({notional:.2f})"

    return True, None


def build_risk_plan(strategy: dict) -> dict | None:
    ok, reason = validate_strategy(strategy)
    if not ok:
        return None

    capital = get_capital()
    risk_percent = get_risk_percent()

    entry = float(strategy["entry"])
    sl = float(strategy["sl"])
    symbol = str(strategy["symbol"]).upper().strip()

    if capital <= 0:
        return None

    if risk_percent <= 0 or risk_percent > 100:
        return None

    risk_amount = capital * (risk_percent / 100.0)
    stop_distance = abs(entry - sl)

    if stop_distance <= 0:
        return None

    position_size = risk_amount / stop_distance
    notional = position_size * entry

    if position_size <= 0:
        return None

    ok, reason = validate_risk_limits(symbol, notional, risk_amount)
    if not ok:
        return None

    return {
        "capital": capital,
        "risk_percent": risk_percent,
        "risk_amount": risk_amount,
        "position_size": position_size,
        "notional": notional,
    }


def get_risk_summary() -> dict:
    today_pnl = get_today_realized_pnl()
    limit_hit, _ = is_daily_loss_limit_hit()

    return {
        "capital": float(settings.RISK_CAPITAL_USDT),
        "risk_percent": float(settings.RISK_PER_TRADE_PERCENT),
        "max_open_trades": int(settings.MAX_OPEN_TRADES),
        "max_notional_per_trade": float(settings.MAX_NOTIONAL_PER_TRADE),
        "daily_loss_limit_usdt": float(settings.DAILY_LOSS_LIMIT_USDT),
        "today_realized_pnl": float(today_pnl),
        "daily_loss_limit_hit": bool(limit_hit),
        "kill_switch": bool(settings.KILL_SWITCH),
    }