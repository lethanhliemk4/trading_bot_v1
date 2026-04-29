def generate_insights():
    insights = []

    # V1: mock logic (sau sẽ đọc DB thật)

    insights.append({
        "level": "info",
        "title": "System đang hoạt động",
        "message": "Backend đã chạy thành công",
        "action": "NONE"
    })

    insights.append({
        "level": "warning",
        "title": "Chưa kết nối database",
        "message": "Dashboard chưa đọc được dữ liệu trading",
        "action": "CHECK_DB"
    })

    return insights