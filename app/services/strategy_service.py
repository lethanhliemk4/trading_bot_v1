def build_strategy(signal: dict) -> dict:
    entry = float(signal["entry_price"])
    side = signal.get("side", "LONG")
    atr = float(signal.get("atr", 0.0))

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
    reward = abs(tp2 - entry)
    rr = reward / risk if risk != 0 else 0.0

    return {
        "side": side,
        "entry": entry,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,
        "rr": rr,
        "atr": atr,
    }