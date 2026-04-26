import time
from collections import deque
from typing import Deque

from app.config import get_settings
from app.services.live_trade_service import get_latest_live_trades

settings = get_settings()

# memory cache (runtime)
_last_check_ts = 0
_cached_result = (True, None)

# store last N trade results
TRADE_HISTORY_LIMIT = 20


def _get_recent_results(limit: int = TRADE_HISTORY_LIMIT) -> list[float]:
    trades = get_latest_live_trades(limit=limit)

    results = []
    for t in trades:
        if t.status == "CLOSED" and t.result_percent is not None:
            results.append(float(t.result_percent))

    return results


def _check_losing_streak(results: list[float]) -> tuple[bool, str | None]:
    streak = 0
    max_streak = getattr(settings, "MAX_LOSING_STREAK", 3)

    for r in results:
        if r < 0:
            streak += 1
        else:
            break

    if streak >= max_streak:
        return False, f"Losing streak ({streak})"

    return True, None


def _check_winrate(results: list[float]) -> tuple[bool, str | None]:
    if not results:
        return True, None

    wins = sum(1 for r in results if r > 0)
    total = len(results)

    winrate = wins / total

    min_winrate = getattr(settings, "MIN_WINRATE", 0.4)

    if total >= 5 and winrate < min_winrate:
        return False, f"Low winrate ({winrate:.2f})"

    return True, None


def _check_volatility_guard() -> tuple[bool, str | None]:
    # đơn giản: check ATR thấp → skip
    # (có thể nâng cấp sau bằng market data thật)
    min_volatility = getattr(settings, "MIN_MARKET_VOLATILITY", 0.002)

    # placeholder: luôn pass (để không phá bot hiện tại)
    # sau này có thể inject từ scanner
    return True, None


def validate_profit_guard() -> tuple[bool, str | None]:
    global _last_check_ts, _cached_result

    now = time.time()

    # cache 10s tránh spam DB
    if now - _last_check_ts < 10:
        return _cached_result

    results = _get_recent_results()

    ok, reason = _check_losing_streak(results)
    if not ok:
        _cached_result = (False, reason)
        _last_check_ts = now
        return _cached_result

    ok, reason = _check_winrate(results)
    if not ok:
        _cached_result = (False, reason)
        _last_check_ts = now
        return _cached_result

    ok, reason = _check_volatility_guard()
    if not ok:
        _cached_result = (False, reason)
        _last_check_ts = now
        return _cached_result

    _cached_result = (True, None)
    _last_check_ts = now
    return _cached_result