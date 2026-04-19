def calculate_atr(klines: list[dict], period: int = 5) -> float:
    """
    klines: list dict có high, low, close
    cần ít nhất period + 1 nến
    """
    if len(klines) < period + 1:
        return 0.0

    true_ranges = []

    for i in range(1, len(klines)):
        current = klines[i]
        prev = klines[i - 1]

        high = current["high"]
        low = current["low"]
        prev_close = prev["close"]

        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close),
        )
        true_ranges.append(tr)

    recent_tr = true_ranges[-period:]
    if not recent_tr:
        return 0.0

    return sum(recent_tr) / len(recent_tr)
