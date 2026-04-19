import csv
import os
from datetime import datetime, timezone

from app.config import get_settings
from app.db.session import SessionLocal
from app.db.models import PaperTrade

settings = get_settings()


def _normalize_symbol(symbol: str) -> str:
    return str(symbol).upper().strip()


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def create_paper_trade(data: dict):
    db = SessionLocal()
    try:
        if settings.KILL_SWITCH:
            return None

        symbol = _normalize_symbol(data["symbol"])
        side = str(data["side"]).upper().strip()

        if side not in {"LONG", "SHORT"}:
            return None

        entry = _safe_float(data.get("entry_price", data.get("entry")))
        sl = _safe_float(data["sl"])
        tp1 = _safe_float(data["tp1"])
        tp2 = _safe_float(data["tp2"])
        rr = _safe_float(data["rr"])
        risk_amount = _safe_float(data["risk_amount"])
        position_size = _safe_float(data["position_size"])
        notional = _safe_float(data["notional"])

        if entry <= 0 or sl <= 0 or tp1 <= 0 or tp2 <= 0:
            return None

        if risk_amount <= 0 or position_size <= 0 or notional <= 0:
            return None

        existing = (
            db.query(PaperTrade)
            .filter(PaperTrade.symbol == symbol, PaperTrade.status == "OPEN")
            .first()
        )
        if existing:
            return None

        trade = PaperTrade(
            symbol=symbol,
            side=side,
            entry_price=entry,
            sl=sl,
            tp1=tp1,
            tp2=tp2,
            rr=rr,
            risk_amount=risk_amount,
            position_size=position_size,
            notional=notional,
            status="OPEN",
            tp1_hit=False,
            tp1_hit_at=None,
            trailing_sl=None,
            trailing_active=False,
            tp1_closed_size=0.0,
            remaining_size=position_size,
            realized_pnl=0.0,
        )

        db.add(trade)
        db.commit()
        db.refresh(trade)
        return trade
    finally:
        db.close()


def get_open_paper_trades(limit: int = 20):
    db = SessionLocal()
    try:
        return (
            db.query(PaperTrade)
            .filter(PaperTrade.status == "OPEN")
            .order_by(PaperTrade.created_at.desc())
            .limit(limit)
            .all()
        )
    finally:
        db.close()


def get_all_open_paper_trades():
    db = SessionLocal()
    try:
        return (
            db.query(PaperTrade)
            .filter(PaperTrade.status == "OPEN")
            .order_by(PaperTrade.created_at.desc())
            .all()
        )
    finally:
        db.close()


def get_latest_paper_trades(limit: int = 20):
    db = SessionLocal()
    try:
        return (
            db.query(PaperTrade)
            .order_by(PaperTrade.created_at.desc())
            .limit(limit)
            .all()
        )
    finally:
        db.close()


def get_all_paper_trades():
    db = SessionLocal()
    try:
        return db.query(PaperTrade).order_by(PaperTrade.created_at.desc()).all()
    finally:
        db.close()


def partial_close_paper_trade_tp1(trade_id: int, price: float, ratio: float = 0.5):
    db = SessionLocal()
    try:
        trade = db.query(PaperTrade).filter(PaperTrade.id == trade_id).first()
        if not trade or trade.status != "OPEN" or trade.tp1_hit:
            return None

        ratio = _safe_float(ratio)
        price = _safe_float(price)

        if ratio <= 0 or ratio >= 1:
            return None

        if price <= 0:
            return None

        if trade.remaining_size is None or trade.remaining_size <= 0:
            return None

        base_size = trade.remaining_size
        closed_size = min(base_size * ratio, base_size)

        if closed_size <= 0:
            return None

        if trade.side == "LONG":
            pnl = closed_size * (price - trade.entry_price)
        else:
            pnl = closed_size * (trade.entry_price - price)

        trade.tp1_hit = True
        trade.tp1_hit_at = datetime.now(timezone.utc)
        trade.tp1_closed_size = closed_size
        trade.remaining_size = max(base_size - closed_size, 0.0)
        trade.realized_pnl = (trade.realized_pnl or 0.0) + pnl

        db.commit()
        db.refresh(trade)
        return trade
    finally:
        db.close()


def mark_paper_trade_tp1_hit(trade_id: int):
    db = SessionLocal()
    try:
        trade = db.query(PaperTrade).filter(PaperTrade.id == trade_id).first()
        if not trade:
            return None

        if trade.tp1_hit:
            return trade

        trade.tp1_hit = True
        trade.tp1_hit_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(trade)
        return trade
    finally:
        db.close()


def activate_paper_trade_trailing(trade_id: int, trailing_sl: float):
    db = SessionLocal()
    try:
        trade = db.query(PaperTrade).filter(PaperTrade.id == trade_id).first()
        if not trade or trade.status != "OPEN":
            return None

        trailing_sl = _safe_float(trailing_sl)
        if trailing_sl <= 0:
            return None

        trade.trailing_active = True
        trade.trailing_sl = trailing_sl

        db.commit()
        db.refresh(trade)
        return trade
    finally:
        db.close()


def update_paper_trade_trailing_sl(trade_id: int, trailing_sl: float):
    db = SessionLocal()
    try:
        trade = db.query(PaperTrade).filter(PaperTrade.id == trade_id).first()
        if not trade or trade.status != "OPEN" or not trade.trailing_active:
            return None

        trailing_sl = _safe_float(trailing_sl)
        if trailing_sl <= 0:
            return None

        trade.trailing_sl = trailing_sl

        db.commit()
        db.refresh(trade)
        return trade
    finally:
        db.close()


def close_paper_trade(
    trade_id: int, exit_price: float, result_percent: float, close_reason: str
):
    db = SessionLocal()
    try:
        trade = db.query(PaperTrade).filter(PaperTrade.id == trade_id).first()
        if not trade or trade.status != "OPEN":
            return None

        exit_price = _safe_float(exit_price)
        result_percent = _safe_float(result_percent)

        if exit_price <= 0:
            return None

        size = (
            trade.remaining_size
            if trade.remaining_size is not None
            else trade.position_size
        )
        if size is None or size <= 0:
            return None

        if trade.side == "LONG":
            pnl = size * (exit_price - trade.entry_price)
        else:
            pnl = size * (trade.entry_price - exit_price)

        trade.realized_pnl = (trade.realized_pnl or 0.0) + pnl
        trade.exit_price = exit_price
        trade.result_percent = result_percent
        trade.close_reason = close_reason
        trade.status = "CLOSED"
        trade.remaining_size = 0.0
        trade.closed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(trade)
        return trade
    finally:
        db.close()


def clear_paper_trades() -> int:
    db = SessionLocal()
    try:
        count = db.query(PaperTrade).count()
        db.query(PaperTrade).delete()
        db.commit()
        return count
    finally:
        db.close()


def get_paper_trade_stats() -> dict:
    db = SessionLocal()
    try:
        trades = db.query(PaperTrade).all()

        total = len(trades)
        open_count = len([t for t in trades if t.status == "OPEN"])
        closed_trades = [t for t in trades if t.status == "CLOSED"]
        closed_count = len(closed_trades)

        wins = len([t for t in closed_trades if (t.realized_pnl or 0.0) > 0])
        loses = len([t for t in closed_trades if (t.realized_pnl or 0.0) < 0])
        draws = len([t for t in closed_trades if (t.realized_pnl or 0.0) == 0])

        winrate = (wins / closed_count * 100) if closed_count else 0.0

        realized_list = [t.realized_pnl or 0.0 for t in closed_trades]
        avg_result = (sum(realized_list) / len(realized_list)) if realized_list else 0.0
        best_result = max(realized_list) if realized_list else 0.0
        worst_result = min(realized_list) if realized_list else 0.0
        tp1_hits = len([t for t in trades if t.tp1_hit])

        return {
            "total": total,
            "open": open_count,
            "closed": closed_count,
            "wins": wins,
            "loses": loses,
            "draws": draws,
            "winrate": winrate,
            "avg_result": avg_result,
            "best_result": best_result,
            "worst_result": worst_result,
            "tp1_hits": tp1_hits,
        }
    finally:
        db.close()


def get_paper_equity() -> dict:
    db = SessionLocal()
    try:
        start_capital = settings.RISK_CAPITAL_USDT

        closed_trades = db.query(PaperTrade).filter(PaperTrade.status == "CLOSED").all()

        realized_pnl = sum((t.realized_pnl or 0.0) for t in closed_trades)
        closed_count = len(closed_trades)

        current_equity = start_capital + realized_pnl
        avg_pnl_per_trade = realized_pnl / closed_count if closed_count else 0.0

        return {
            "start_capital": start_capital,
            "realized_pnl": realized_pnl,
            "current_equity": current_equity,
            "closed_trades": closed_count,
            "avg_pnl_per_trade": avg_pnl_per_trade,
        }
    finally:
        db.close()


def get_today_realized_pnl() -> float:
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)

        trades = (
            db.query(PaperTrade)
            .filter(
                PaperTrade.status == "CLOSED",
                PaperTrade.closed_at.isnot(None),
                PaperTrade.closed_at >= start,
            )
            .all()
        )

        return sum((t.realized_pnl or 0.0) for t in trades)
    finally:
        db.close()


def is_daily_loss_limit_hit() -> tuple[bool, float]:
    pnl = get_today_realized_pnl()
    if pnl <= -abs(settings.DAILY_LOSS_LIMIT_USDT):
        return True, pnl
    return False, pnl


def export_paper_trades_csv(output_dir: str = "/tmp") -> str | None:
    trades = get_all_paper_trades()
    if not trades:
        return None

    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(output_dir, f"paper_trades_{timestamp}.csv")

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "id",
                "symbol",
                "side",
                "entry_price",
                "sl",
                "tp1",
                "tp2",
                "rr",
                "risk_amount",
                "position_size",
                "notional",
                "status",
                "exit_price",
                "result_percent",
                "close_reason",
                "tp1_hit",
                "tp1_hit_at",
                "trailing_sl",
                "trailing_active",
                "tp1_closed_size",
                "remaining_size",
                "realized_pnl",
                "created_at",
                "updated_at",
                "closed_at",
            ]
        )

        for t in trades:
            writer.writerow(
                [
                    t.id,
                    t.symbol,
                    t.side,
                    t.entry_price,
                    t.sl,
                    t.tp1,
                    t.tp2,
                    t.rr,
                    t.risk_amount,
                    t.position_size,
                    t.notional,
                    t.status,
                    t.exit_price,
                    t.result_percent,
                    t.close_reason,
                    t.tp1_hit,
                    t.tp1_hit_at,
                    t.trailing_sl,
                    t.trailing_active,
                    t.tp1_closed_size,
                    t.remaining_size,
                    t.realized_pnl,
                    t.created_at,
                    t.updated_at,
                    t.closed_at,
                ]
            )

    return filepath
