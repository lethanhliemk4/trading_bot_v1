from sqlalchemy import text
from app.db.session import SessionLocal


def get_overview():
    db = SessionLocal()

    try:
        open_trades = db.execute(
            text("SELECT COUNT(*) FROM live_trades WHERE status='OPEN'")
        ).scalar() or 0

        today_pnl = db.execute(
            text("""
                SELECT COALESCE(SUM(realized_pnl), 0)
                FROM live_trades
                WHERE DATE(created_at) = CURDATE()
            """)
        ).scalar() or 0

        signal_count = db.execute(
            text("""
                SELECT COUNT(*)
                FROM signals
                WHERE created_at >= NOW() - INTERVAL 1 HOUR
            """)
        ).scalar() or 0

        bot_state = db.execute(
            text("SELECT trade_mode FROM bot_state ORDER BY id DESC LIMIT 1")
        ).scalar()

        return {
            "market_state": "VOLATILE" if signal_count > 20 else "ACTIVE" if signal_count > 5 else "QUIET",
            "risk_status": "HIGH" if open_trades >= 3 else "MEDIUM" if open_trades > 0 else "LOW",
            "strategy_status": "WEAK" if today_pnl < 0 else "GOOD" if today_pnl > 0 else "NEUTRAL",
            "open_trades": open_trades,
            "today_pnl": float(today_pnl),
            "recommendation": "REDUCE_RISK" if open_trades >= 3 else "NORMAL",
            "bot_mode": bot_state,
        }

    except Exception as e:
        return {
            "market_state": "UNKNOWN",
            "risk_status": "UNKNOWN",
            "strategy_status": "UNKNOWN",
            "open_trades": 0,
            "today_pnl": 0.0,
            "recommendation": "CHECK_DB",
            "bot_mode": None,
            "error": str(e),
        }

    finally:
        db.close()


def get_insights():
    return [
        {
            "level": "warning",
            "title": "Database chưa kết nối",
            "message": "Backend chưa đọc được DB thật. Kiểm tra DB_HOST, DB_PORT, DB_USER, DB_PASSWORD.",
            "action": "CHECK_DB"
        }
    ]