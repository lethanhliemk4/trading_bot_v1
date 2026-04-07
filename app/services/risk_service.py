import os


def get_capital() -> float:
    try:
        return float(os.getenv("RISK_CAPITAL_USDT", "1000"))
    except Exception:
        return 1000.0


def get_risk_percent() -> float:
    try:
        return float(os.getenv("RISK_PER_TRADE_PERCENT", "1"))
    except Exception:
        return 1.0


def build_risk_plan(strategy: dict) -> dict:
    capital = get_capital()
    risk_percent = get_risk_percent()

    entry = float(strategy["entry"])
    sl = float(strategy["sl"])

    risk_amount = capital * (risk_percent / 100.0)
    stop_distance = abs(entry - sl)

    if stop_distance <= 0:
        position_size = 0.0
    else:
        position_size = risk_amount / stop_distance

    notional = position_size * entry

    return {
        "capital": capital,
        "risk_percent": risk_percent,
        "risk_amount": risk_amount,
        "position_size": position_size,
        "notional": notional,
    }