def build_strategy(signal: dict) -> dict:
    symbol = str(signal.get("symbol", "")).upper().strip()
    entry = float(signal.get("entry_price", 0.0) or 0.0)
    side = str(signal.get("side", "LONG")).upper().strip()
    atr = float(signal.get("atr", 0.0) or 0.0)

    if side not in {"LONG", "SHORT"}:
        side = "LONG"

    if entry <= 0:
        entry = 1.0

    # fallback nếu ATR quá nhỏ
    if atr <= 0:
        atr = entry * 0.005  # 0.5%

    sl_distance = atr * 1.5
    tp1_distance = sl_distance * 1.5
    tp2_distance = sl_distance * 2.5

    if side == "SHORT":
        sl = entry + sl_distance
        tp1 = entry - tp1_distance
        tp2 = entry - tp2_distance
    else:
        sl = entry - sl_distance
        tp1 = entry + tp1_distance
        tp2 = entry + tp2_distance

    risk = abs(entry - sl)
    reward_tp1 = abs(tp1 - entry)
    reward_tp2 = abs(tp2 - entry)

    rr_tp1 = reward_tp1 / risk if risk != 0 else 0.0
    rr_tp2 = reward_tp2 / risk if risk != 0 else 0.0

    return {
        "symbol": symbol,
        "side": side,
        "entry": entry,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,
        "rr": rr_tp2,
        "rr_tp1": rr_tp1,
        "rr_tp2": rr_tp2,
        "atr": atr,
        "sl_distance": sl_distance,
        "tp1_distance": tp1_distance,
        "tp2_distance": tp2_distance,
        "risk_per_unit": risk,
        "reward_tp1": reward_tp1,
        "reward_tp2": reward_tp2,
        "is_valid": risk > 0 and entry > 0,
    }