from app.config import get_settings

settings = get_settings()


def build_strategy(signal: dict) -> dict:
    symbol = str(signal.get("symbol", "")).upper().strip()
    entry = float(signal.get("entry_price", 0.0) or 0.0)
    side = str(signal.get("side", "LONG")).upper().strip()
    atr = float(signal.get("atr", 0.0) or 0.0)

    score = float(signal.get("score", 0.0) or 0.0)
    quote_volume_5m = float(signal.get("quote_volume_5m", 0.0) or 0.0)
    volume_spike_ratio = float(signal.get("volume_spike_ratio", 0.0) or 0.0)

    if side not in {"LONG", "SHORT"}:
        side = "LONG"

    base_invalid = {
        "symbol": symbol,
        "side": side,
        "entry": entry,
        "sl": 0.0,
        "tp1": 0.0,
        "tp2": 0.0,
        "rr": 0.0,
        "rr_tp1": 0.0,
        "rr_tp2": 0.0,
        "atr": atr,
        "atr_ratio": 0.0,
        "sl_distance": 0.0,
        "tp1_distance": 0.0,
        "tp2_distance": 0.0,
        "risk_per_unit": 0.0,
        "reward_tp1": 0.0,
        "reward_tp2": 0.0,
        "score": score,
        "quote_volume_5m": quote_volume_5m,
        "volume_spike_ratio": volume_spike_ratio,
        "sl_atr_multiplier": float(settings.STRATEGY_SL_ATR_MULTIPLIER),
        "tp1_rr_config": float(settings.STRATEGY_TP1_RR),
        "tp2_rr_config": float(settings.STRATEGY_TP2_RR),
        "is_valid": False,
        "invalid_reason": None,
    }

    if not symbol:
        base_invalid["invalid_reason"] = "missing symbol"
        return base_invalid

    if entry <= 0:
        base_invalid["invalid_reason"] = "entry_price <= 0"
        return base_invalid

    if atr <= 0:
        base_invalid["invalid_reason"] = "atr <= 0"
        return base_invalid

    atr_ratio = atr / entry
    base_invalid["atr_ratio"] = atr_ratio

    if score < settings.STRATEGY_MIN_SCORE:
        base_invalid["invalid_reason"] = f"score too low ({score})"
        return base_invalid

    if quote_volume_5m < settings.STRATEGY_MIN_QUOTE_VOLUME_5M:
        base_invalid["invalid_reason"] = f"volume too low ({quote_volume_5m})"
        return base_invalid

    if volume_spike_ratio < settings.STRATEGY_MIN_VOLUME_SPIKE_RATIO:
        base_invalid["invalid_reason"] = f"spike too low ({volume_spike_ratio})"
        return base_invalid

    if atr_ratio < settings.STRATEGY_MIN_ATR_RATIO:
        base_invalid["invalid_reason"] = f"atr ratio too low ({atr_ratio:.6f})"
        return base_invalid

    sl_distance = atr * settings.STRATEGY_SL_ATR_MULTIPLIER
    tp1_distance = sl_distance * settings.STRATEGY_TP1_RR
    tp2_distance = sl_distance * settings.STRATEGY_TP2_RR

    if sl_distance <= 0:
        base_invalid["invalid_reason"] = "sl_distance <= 0"
        return base_invalid

    if tp1_distance <= 0:
        base_invalid["invalid_reason"] = "tp1_distance <= 0"
        return base_invalid

    if tp2_distance <= 0:
        base_invalid["invalid_reason"] = "tp2_distance <= 0"
        return base_invalid

    if tp2_distance <= tp1_distance:
        base_invalid["invalid_reason"] = "tp2_distance must be greater than tp1_distance"
        return base_invalid

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

    if risk <= 0:
        base_invalid["invalid_reason"] = "risk <= 0"
        return base_invalid

    if reward_tp1 <= 0:
        base_invalid["invalid_reason"] = "reward_tp1 <= 0"
        return base_invalid

    if reward_tp2 <= 0:
        base_invalid["invalid_reason"] = "reward_tp2 <= 0"
        return base_invalid

    if side == "LONG":
        if sl >= entry:
            base_invalid["invalid_reason"] = "SL must be below entry for LONG"
            return base_invalid
        if tp1 <= entry:
            base_invalid["invalid_reason"] = "TP1 must be above entry for LONG"
            return base_invalid
        if tp2 <= tp1:
            base_invalid["invalid_reason"] = "TP2 must be above TP1 for LONG"
            return base_invalid
    else:
        if sl <= entry:
            base_invalid["invalid_reason"] = "SL must be above entry for SHORT"
            return base_invalid
        if tp1 >= entry:
            base_invalid["invalid_reason"] = "TP1 must be below entry for SHORT"
            return base_invalid
        if tp2 >= tp1:
            base_invalid["invalid_reason"] = "TP2 must be below TP1 for SHORT"
            return base_invalid

    rr_tp1 = reward_tp1 / risk if risk > 0 else 0.0
    rr_tp2 = reward_tp2 / risk if risk > 0 else 0.0

    if rr_tp1 <= 0:
        base_invalid["invalid_reason"] = "rr_tp1 <= 0"
        return base_invalid

    if rr_tp2 <= 0:
        base_invalid["invalid_reason"] = "rr_tp2 <= 0"
        return base_invalid

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
        "atr_ratio": atr_ratio,
        "sl_distance": sl_distance,
        "tp1_distance": tp1_distance,
        "tp2_distance": tp2_distance,
        "risk_per_unit": risk,
        "reward_tp1": reward_tp1,
        "reward_tp2": reward_tp2,
        "score": score,
        "quote_volume_5m": quote_volume_5m,
        "volume_spike_ratio": volume_spike_ratio,
        "sl_atr_multiplier": float(settings.STRATEGY_SL_ATR_MULTIPLIER),
        "tp1_rr_config": float(settings.STRATEGY_TP1_RR),
        "tp2_rr_config": float(settings.STRATEGY_TP2_RR),
        "is_valid": True,
        "invalid_reason": None,
    }