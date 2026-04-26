from datetime import datetime, timedelta, timezone

from app.services.live_trade_service import get_latest_live_trades


def _normalize_datetime(value):
    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def get_recent_performance(days: int = 1, limit: int = 300) -> dict:
    """
    Return recent LIVE closed-trade performance.

    Used by Telegram command:
    /perf

    Notes:
    - Only CLOSED live trades are counted.
    - Uses closed_at as the time filter.
    - Keeps this service read-only and safe for production.
    """

    if days <= 0:
        days = 1

    if limit <= 0:
        limit = 300

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)

    trades = get_latest_live_trades(limit=limit)

    total = 0
    wins = 0
    loses = 0
    draws = 0

    total_pnl = 0.0
    best_pnl = 0.0
    worst_pnl = 0.0
    best_result_percent = 0.0
    worst_result_percent = 0.0

    counted_any = False

    for trade in trades:
        if trade.status != "CLOSED":
            continue

        closed_at = _normalize_datetime(trade.closed_at)
        if closed_at is None:
            continue

        if closed_at < cutoff:
            continue

        realized_pnl = float(trade.realized_pnl or 0.0)
        result_percent = float(trade.result_percent or 0.0)

        total += 1
        total_pnl += realized_pnl

        if result_percent > 0:
            wins += 1
        elif result_percent < 0:
            loses += 1
        else:
            draws += 1

        if not counted_any:
            best_pnl = realized_pnl
            worst_pnl = realized_pnl
            best_result_percent = result_percent
            worst_result_percent = result_percent
            counted_any = True
        else:
            best_pnl = max(best_pnl, realized_pnl)
            worst_pnl = min(worst_pnl, realized_pnl)
            best_result_percent = max(best_result_percent, result_percent)
            worst_result_percent = min(worst_result_percent, result_percent)

    winrate = (wins / total * 100.0) if total > 0 else 0.0
    avg_pnl = (total_pnl / total) if total > 0 else 0.0

    return {
        "days": int(days),
        "limit": int(limit),
        "total": int(total),
        "wins": int(wins),
        "loses": int(loses),
        "draws": int(draws),
        "winrate": float(winrate),
        "pnl": float(total_pnl),
        "avg_pnl": float(avg_pnl),
        "best_pnl": float(best_pnl),
        "worst_pnl": float(worst_pnl),
        "best_result_percent": float(best_result_percent),
        "worst_result_percent": float(worst_result_percent),
        "from": cutoff.isoformat(),
        "to": now.isoformat(),
    }
