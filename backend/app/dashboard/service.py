from sqlalchemy import text
from app.db.session import SessionLocal
from app.dashboard.insight_engine import generate_insights


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

        market_state = "VOLATILE" if signal_count > 20 else "ACTIVE" if signal_count > 5 else "QUIET"
        risk_status = "HIGH" if open_trades >= 3 else "MEDIUM" if open_trades > 0 else "LOW"
        strategy_status = "WEAK" if today_pnl < 0 else "GOOD" if today_pnl > 0 else "NEUTRAL"

        return {
            "market_state": market_state,
            "risk_status": risk_status,
            "strategy_status": strategy_status,
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
    db = SessionLocal()

    try:
        return generate_insights(db)

    except Exception as e:
        return [
            {
                "level": "danger",
                "title": "Không đọc được database",
                "message": str(e),
                "action": "CHECK_DB"
            }
        ]

    finally:
        db.close()

def get_failed_live_trades():
    db = SessionLocal()

    try:
        rows = db.execute(
            text("""
                SELECT
                    id,
                    symbol,
                    side,
                    status,
                    entry_price,
                    notional,
                    fail_reason,
                    created_at
                FROM live_trades
                WHERE fail_reason IS NOT NULL
                ORDER BY created_at DESC
                LIMIT 20
            """)
        ).mappings().all()

        return [dict(row) for row in rows]

    finally:
        db.close()

def get_trading_summary():
    db = SessionLocal()

    try:
        today_trades = db.execute(
            text("""
                SELECT COUNT(*)
                FROM live_trades
                WHERE DATE(created_at) = CURDATE()
            """)
        ).scalar() or 0

        failed_trades = db.execute(
            text("""
                SELECT COUNT(*)
                FROM live_trades
                WHERE DATE(created_at) = CURDATE()
                  AND fail_reason IS NOT NULL
            """)
        ).scalar() or 0

        today_pnl = db.execute(
            text("""
                SELECT COALESCE(SUM(realized_pnl), 0)
                FROM live_trades
                WHERE DATE(created_at) = CURDATE()
            """)
        ).scalar() or 0

        avg_notional = db.execute(
            text("""
                SELECT COALESCE(AVG(notional), 0)
                FROM live_trades
                WHERE DATE(created_at) = CURDATE()
            """)
        ).scalar() or 0

        most_common_fail_reason = db.execute(
            text("""
                SELECT fail_reason
                FROM live_trades
                WHERE fail_reason IS NOT NULL
                GROUP BY fail_reason
                ORDER BY COUNT(*) DESC
                LIMIT 1
            """)
        ).scalar()

        fail_rate = 0
        if today_trades > 0:
            fail_rate = round((failed_trades / today_trades) * 100, 2)

        return {
            "today_trades": today_trades,
            "failed_trades": failed_trades,
            "fail_rate": fail_rate,
            "today_pnl": round(float(today_pnl), 4),
            "avg_notional": round(float(avg_notional), 4),
            "most_common_fail_reason": most_common_fail_reason,
        }

    finally:
        db.close()


def get_trade_analytics():
    db = SessionLocal()

    try:
        result = db.execute(text("""
            SELECT 
                symbol,
                COUNT(*) AS total,
                SUM(CASE WHEN fail_reason IS NOT NULL THEN 1 ELSE 0 END) AS failed,
                ROUND(AVG(notional), 4) AS avg_notional
            FROM live_trades
            WHERE DATE(created_at) = CURDATE()
            GROUP BY symbol
            ORDER BY total DESC
            LIMIT 10
        """)).fetchall()

        return [
            {
                "symbol": row[0],
                "total": row[1],
                "failed": row[2],
                "avg_notional": float(row[3] or 0),
            }
            for row in result
        ]

    finally:
        db.close()

def get_recent_live_trades():
    db = SessionLocal()

    try:
        rows = db.execute(
            text("""
                SELECT
                    id,
                    symbol,
                    side,
                    status,
                    entry_price,
                    notional,
                    realized_pnl,
                    close_reason,
                    created_at
                FROM live_trades
                ORDER BY created_at DESC
                LIMIT 20
            """)
        ).mappings().all()

        return [dict(row) for row in rows]

    finally:
        db.close()