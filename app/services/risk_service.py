from datetime import datetime, timezone

from app.config import get_settings
from app.db.models import LiveTrade
from app.db.session import SessionLocal
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


def validate_risk_limits(
    symbol: str,
    notional: float,
    risk_amount: float,
) -> tuple[bool, str | None]:
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


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _start_of_today_utc() -> datetime:
    now = _utcnow()
    return datetime(now.year, now.month, now.day, tzinfo=timezone.utc)


def get_today_live_realized_pnl() -> float:
    db = SessionLocal()
    try:
        start_of_day = _start_of_today_utc()

        trades = (
            db.query(LiveTrade)
            .filter(
                LiveTrade.status == "CLOSED",
                LiveTrade.closed_at.isnot(None),
                LiveTrade.closed_at >= start_of_day,
            )
            .all()
        )

        return float(sum(float(t.realized_pnl or 0.0) for t in trades))
    finally:
        db.close()


def get_today_live_trade_count() -> int:
    db = SessionLocal()
    try:
        start_of_day = _start_of_today_utc()

        count = (
            db.query(LiveTrade)
            .filter(
                LiveTrade.created_at >= start_of_day,
                LiveTrade.status.in_(["OPEN", "CLOSED"]),
            )
            .count()
        )

        return int(count)
    finally:
        db.close()


def get_open_live_trades_count() -> int:
    db = SessionLocal()
    try:
        return int(db.query(LiveTrade).filter(LiveTrade.status == "OPEN").count())
    finally:
        db.close()


def has_open_live_trade_for_symbol(symbol: str) -> bool:
    db = SessionLocal()
    try:
        trade = (
            db.query(LiveTrade)
            .filter(
                LiveTrade.status == "OPEN",
                LiveTrade.symbol == str(symbol).upper().strip(),
            )
            .first()
        )
        return trade is not None
    finally:
        db.close()


def is_live_daily_loss_limit_hit() -> tuple[bool, float]:
    today_pnl = get_today_live_realized_pnl()
    limit_hit = today_pnl <= -abs(float(settings.LIVE_DAILY_LOSS_LIMIT_USDT))
    return limit_hit, float(today_pnl)


def validate_live_risk_limits(
    symbol: str,
    notional: float,
    risk_amount: float,
) -> tuple[bool, str | None]:
    normalized_symbol = str(symbol).upper().strip()

    if settings.KILL_SWITCH:
        return False, "KILL_SWITCH active"

    if not normalized_symbol:
        return False, "Missing symbol"

    if risk_amount <= 0:
        return False, "Invalid live risk amount"

    limit_hit, today_pnl = is_live_daily_loss_limit_hit()
    if limit_hit:
        return False, f"Live daily loss limit hit ({today_pnl:+.2f})"

    today_count = get_today_live_trade_count()
    if today_count >= settings.LIVE_MAX_TRADES_PER_DAY:
        return False, f"Live max trades/day reached ({today_count})"

    open_live_trades = get_open_live_trades_count()
    if open_live_trades >= settings.LIVE_MAX_OPEN_TRADES:
        return False, "Live max open trades reached"

    if has_open_live_trade_for_symbol(normalized_symbol):
        return False, f"Live trade already open for {normalized_symbol}"

    if notional <= 0:
        return False, "Invalid live notional"

    if notional > settings.LIVE_MAX_NOTIONAL_PER_TRADE:
        return False, f"Live notional too high ({notional:.2f})"

    if risk_amount > settings.LIVE_DAILY_LOSS_LIMIT_USDT:
        return False, (
            f"Live risk amount too high "
            f"({risk_amount:.2f} > {settings.LIVE_DAILY_LOSS_LIMIT_USDT:.2f})"
        )

    return True, None


def calculate_position_size(
    entry: float,
    sl: float,
    capital: float,
    risk_percent: float,
) -> dict | None:
    if entry <= 0 or sl <= 0:
        return None

    if capital <= 0:
        return None

    if risk_percent <= 0 or risk_percent > 100:
        return None

    stop_distance = abs(entry - sl)
    if stop_distance <= 0:
        return None

    risk_amount = capital * (risk_percent / 100.0)
    if risk_amount <= 0:
        return None

    position_size = risk_amount / stop_distance
    if position_size <= 0:
        return None

    notional = position_size * entry
    if notional <= 0:
        return None

    return {
        "capital": capital,
        "risk_percent": risk_percent,
        "risk_amount": risk_amount,
        "stop_distance": stop_distance,
        "position_size": position_size,
        "notional": notional,
    }


def build_risk_plan_with_reason(strategy: dict) -> tuple[dict | None, str | None]:
    ok, reason = validate_strategy(strategy)
    if not ok:
        return None, reason

    capital = get_capital()
    risk_percent = get_risk_percent()

    entry = float(strategy["entry"])
    sl = float(strategy["sl"])
    symbol = str(strategy["symbol"]).upper().strip()
    side = str(strategy["side"]).upper().strip()

    sizing = calculate_position_size(
        entry=entry,
        sl=sl,
        capital=capital,
        risk_percent=risk_percent,
    )
    if not sizing:
        return None, "Position sizing failed"

    ok, reason = validate_risk_limits(
        symbol=symbol,
        notional=float(sizing["notional"]),
        risk_amount=float(sizing["risk_amount"]),
    )
    if not ok:
        return None, reason

    tp1 = float(strategy["tp1"])
    tp2 = float(strategy["tp2"])

    reward_tp1 = abs(tp1 - entry)
    reward_tp2 = abs(tp2 - entry)

    rr_tp1 = (
        reward_tp1 / sizing["stop_distance"] if sizing["stop_distance"] > 0 else 0.0
    )
    rr_tp2 = (
        reward_tp2 / sizing["stop_distance"] if sizing["stop_distance"] > 0 else 0.0
    )

    return {
        "capital": float(sizing["capital"]),
        "risk_percent": float(sizing["risk_percent"]),
        "risk_amount": float(sizing["risk_amount"]),
        "position_size": float(sizing["position_size"]),
        "notional": float(sizing["notional"]),
        "stop_distance": float(sizing["stop_distance"]),
        "entry": float(entry),
        "sl": float(sl),
        "tp1": float(tp1),
        "tp2": float(tp2),
        "symbol": symbol,
        "side": side,
        "rr_tp1": float(rr_tp1),
        "rr_tp2": float(rr_tp2),
        "reason": None,
    }, None


def build_risk_plan(strategy: dict) -> dict | None:
    plan, _ = build_risk_plan_with_reason(strategy)
    return plan


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


def get_live_risk_summary() -> dict:
    today_pnl = get_today_live_realized_pnl()
    limit_hit, _ = is_live_daily_loss_limit_hit()

    return {
        "max_open_trades": int(settings.LIVE_MAX_OPEN_TRADES),
        "max_notional_per_trade": float(settings.LIVE_MAX_NOTIONAL_PER_TRADE),
        "max_trades_per_day": int(settings.LIVE_MAX_TRADES_PER_DAY),
        "today_trade_count": int(get_today_live_trade_count()),
        "daily_loss_limit_usdt": float(settings.LIVE_DAILY_LOSS_LIMIT_USDT),
        "live_min_free_usdt": float(settings.LIVE_MIN_FREE_USDT),
        "today_realized_pnl": float(today_pnl),
        "daily_loss_limit_hit": bool(limit_hit),
        "kill_switch": bool(settings.KILL_SWITCH),
    }