from sqlalchemy import text


def generate_insights(db):
    insights = []

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

    failed_trades = db.execute(
        text("""
            SELECT COUNT(*)
            FROM live_trades
            WHERE fail_reason IS NOT NULL
        """)
    ).scalar() or 0

    signal_1h = db.execute(
        text("""
            SELECT COUNT(*)
            FROM signals
            WHERE created_at >= NOW() - INTERVAL 1 HOUR
        """)
    ).scalar() or 0

    bot_mode = db.execute(
        text("SELECT trade_mode FROM bot_state ORDER BY id DESC LIMIT 1")
    ).scalar()

    if bot_mode == "LIVE":
        insights.append({
            "level": "warning",
            "title": "Bot đang ở chế độ LIVE",
            "message": "Dashboard đang đọc dữ liệu live. Cần theo dõi risk thường xuyên.",
            "action": "MONITOR_RISK"
        })

    if open_trades > 0:
        insights.append({
            "level": "warning",
            "title": "Đang có lệnh live mở",
            "message": f"Hiện có {open_trades} lệnh đang mở.",
            "action": "CHECK_OPEN_TRADES"
        })
    else:
        insights.append({
            "level": "info",
            "title": "Không có lệnh live đang mở",
            "message": "Risk hiện tại thấp vì không có vị thế live đang chạy.",
            "action": "NORMAL"
        })

    if today_pnl < 0:
        insights.append({
            "level": "danger",
            "title": "PnL hôm nay đang âm",
            "message": f"PnL hôm nay đang là {float(today_pnl):.4f} USDT.",
            "action": "REDUCE_RISK"
        })

    if failed_trades > 0:
        insights.append({
            "level": "warning",
            "title": "Có live trade bị lỗi",
            "message": f"Có {failed_trades} trade có fail_reason.",
            "action": "CHECK_LOGS"
        })

    if signal_1h == 0:
        insights.append({
            "level": "info",
            "title": "Market đang yên tĩnh",
            "message": "Không có signal trong 1 giờ gần nhất.",
            "action": "WAIT"
        })
    elif signal_1h > 20:
        insights.append({
            "level": "warning",
            "title": "Market biến động mạnh",
            "message": f"Có {signal_1h} signals trong 1 giờ gần nhất.",
            "action": "REDUCE_FREQUENCY"
        })

    return insights