from app.config import get_settings
from app.services.performance_service import get_recent_performance
from app.services.trade_mode_service import set_trade_mode

settings = get_settings()


def _get_auto_stop_enabled() -> bool:
    return bool(getattr(settings, "ENABLE_AUTO_STOP", True))


def _get_max_daily_loss() -> float:
    value = float(getattr(settings, "AUTO_STOP_MAX_DAILY_LOSS", -5.0))

    # Accept both -5 and 5 from .env, always convert to negative threshold.
    if value > 0:
        value = -abs(value)

    return value


def _get_min_winrate() -> float:
    value = float(getattr(settings, "AUTO_STOP_MIN_WINRATE", 0.30))

    # Accept 30 or 0.30 from .env.
    if value > 1:
        value = value / 100.0

    if value < 0:
        value = 0.0

    if value > 1:
        value = 1.0

    return value


def _get_min_trades() -> int:
    value = int(getattr(settings, "AUTO_STOP_MIN_TRADES", 5))
    return max(value, 1)


def check_auto_stop(days: int = 1) -> tuple[bool, str | None]:
    """
    Check whether LIVE auto trading should be stopped.

    Returns:
        (should_stop, reason)

    Safety behavior:
    - If ENABLE_AUTO_STOP=false, always returns safe.
    - Daily loss threshold accepts either -5 or 5 in env.
    - Winrate threshold accepts either 0.30 or 30 in env.
    """

    if not _get_auto_stop_enabled():
        return False, None

    perf = get_recent_performance(days=days)

    max_daily_loss = _get_max_daily_loss()
    min_winrate = _get_min_winrate()
    min_trades = _get_min_trades()

    pnl = float(perf.get("pnl", 0.0) or 0.0)
    total = int(perf.get("total", 0) or 0)
    winrate_percent = float(perf.get("winrate", 0.0) or 0.0)
    winrate_ratio = winrate_percent / 100.0

    if pnl <= max_daily_loss:
        return True, (
            f"Auto stop daily loss hit "
            f"({pnl:+.2f} <= {max_daily_loss:+.2f} USDT)"
        )

    if total >= min_trades and winrate_ratio < min_winrate:
        return True, (
            f"Auto stop low winrate "
            f"({winrate_percent:.2f}% < {min_winrate * 100:.2f}% after {total} trades)"
        )

    return False, None


def trigger_auto_stop(days: int = 1) -> tuple[bool, str | None]:
    """
    Stop auto trading by setting trade mode OFF when auto-stop condition is hit.
    """

    should_stop, reason = check_auto_stop(days=days)

    if not should_stop:
        return False, None

    set_trade_mode("OFF")
    return True, reason


def get_auto_stop_status(days: int = 1) -> dict:
    """
    Read-only status helper for future Telegram/dashboard use.
    """

    enabled = _get_auto_stop_enabled()
    max_daily_loss = _get_max_daily_loss()
    min_winrate = _get_min_winrate()
    min_trades = _get_min_trades()
    should_stop, reason = check_auto_stop(days=days)
    perf = get_recent_performance(days=days)

    return {
        "enabled": bool(enabled),
        "should_stop": bool(should_stop),
        "reason": reason,
        "days": int(days),
        "max_daily_loss": float(max_daily_loss),
        "min_winrate": float(min_winrate),
        "min_trades": int(min_trades),
        "performance": perf,
    }
