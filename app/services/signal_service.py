from sqlalchemy import desc, text

from app.db.session import SessionLocal
from app.db.models import Signal


def save_signal(data: dict):
    db = SessionLocal()
    try:
        signal = Signal(
            symbol=data["symbol"],
            score=data["score"],
            price_change_5m=data["price_change_5m"],
            volume_5m=data["quote_volume_5m"],
            volume_spike=data["volume_spike_ratio"],
            entry_price=data["entry_price"],
            status="pending",
        )
        db.add(signal)
        db.commit()
    finally:
        db.close()


def get_latest_signals(limit: int = 10):
    db = SessionLocal()
    try:
        return (
            db.query(Signal)
            .order_by(desc(Signal.created_at))
            .limit(limit)
            .all()
        )
    finally:
        db.close()


def get_top_signals(limit: int = 10):
    db = SessionLocal()
    try:
        return (
            db.query(Signal)
            .order_by(desc(Signal.score))
            .limit(limit)
            .all()
        )
    finally:
        db.close()


def get_pending_signals(limit: int = 20):
    db = SessionLocal()
    try:
        return (
            db.query(Signal)
            .filter(Signal.status == "pending")
            .order_by(Signal.created_at.asc())
            .limit(limit)
            .all()
        )
    finally:
        db.close()


def update_performance(signal_id: int, data: dict):
    db = SessionLocal()
    try:
        s = db.query(Signal).filter(Signal.id == signal_id).first()
        if not s:
            return

        if "result_5m" in data:
            s.result_5m = data["result_5m"]
            s.checked_5m_at = db.execute(text("SELECT NOW()")).scalar()

        if "result_15m" in data:
            s.result_15m = data["result_15m"]
            s.checked_15m_at = db.execute(text("SELECT NOW()")).scalar()

        if "max_profit" in data:
            s.max_profit = data["max_profit"]

        if "max_drawdown" in data:
            s.max_drawdown = data["max_drawdown"]

        if s.result_15m is not None:
            s.status = "done"

        db.commit()
    finally:
        db.close()


def _timeframe_stats(signals, attr_name: str):
    values = []
    wins = 0
    loses = 0
    draws = 0

    for s in signals:
        value = getattr(s, attr_name)
        if value is None:
            continue

        values.append(value)

        if value > 0:
            wins += 1
        elif value < 0:
            loses += 1
        else:
            draws += 1

    total = len(values)
    winrate = (wins / total * 100) if total else 0.0
    avg = sum(values) / total if total else 0.0

    return {
        "total": total,
        "wins": wins,
        "loses": loses,
        "draws": draws,
        "winrate": winrate,
        "avg": avg,
    }


def get_stats():
    db = SessionLocal()
    try:
        signals = db.query(Signal).all()

        stats_5m = _timeframe_stats(signals, "result_5m")
        stats_15m = _timeframe_stats(signals, "result_15m")

        done_signals = [s for s in signals if s.status == "done"]
        done_total = len(done_signals)

        avg_max_profit = (
            sum((s.max_profit or 0.0) for s in done_signals) / done_total
            if done_total else 0.0
        )
        avg_max_drawdown = (
            sum((s.max_drawdown or 0.0) for s in done_signals) / done_total
            if done_total else 0.0
        )

        return {
            "five_min": stats_5m,
            "fifteen_min": stats_15m,
            "done_total": done_total,
            "avg_max_profit": avg_max_profit,
            "avg_max_drawdown": avg_max_drawdown,
        }
    finally:
        db.close()


def delete_last_signal() -> str | None:
    db = SessionLocal()
    try:
        signal = (
            db.query(Signal)
            .order_by(desc(Signal.created_at), desc(Signal.id))
            .first()
        )
        if not signal:
            return None

        symbol = signal.symbol
        db.delete(signal)
        db.commit()
        return symbol
    finally:
        db.close()


def clear_signals() -> int:
    db = SessionLocal()
    try:
        count = db.query(Signal).count()
        db.query(Signal).delete()
        db.commit()
        return count
    finally:
        db.close()