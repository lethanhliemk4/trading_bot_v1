import asyncio
import logging
import random
from typing import Any

from app.market.rest_client import get_usdt_symbols, get_klines
from app.services.watchlist_service import get_watchlist_symbols
from app.services.indicator_service import calculate_atr

logger = logging.getLogger(__name__)

MIN_QUOTE_VOLUME_5M = 100_000
MIN_PRICE_CHANGE_5M = 0.5
MIN_VOLUME_SPIKE_RATIO = 1.2
MAX_SYMBOLS_PER_SCAN = 80


def parse_kline(kline: list[Any]) -> dict:
    return {
        "open": float(kline[1]),
        "high": float(kline[2]),
        "low": float(kline[3]),
        "close": float(kline[4]),
        "quote_volume": float(kline[7]),
    }


def calc_price_change_percent(open_price, close_price):
    return ((close_price - open_price) / open_price) * 100 if open_price else 0


def calc_volume_spike(current, prev):
    avg = sum(prev) / len(prev) if prev else 0
    return current / avg if avg else 0


def calc_score(change, spike):
    score = 0
    abs_change = abs(change)

    if abs_change >= 2:
        score += 40
    if spike >= 2:
        score += 30
    if abs_change >= 4:
        score += 20
    if spike >= 3:
        score += 10

    return min(score, 100)


async def scan_one(symbol: str):
    try:
        symbol = symbol.upper().strip()

        raw = await get_klines(symbol, limit=10)
        if len(raw) < 6:
            return None

        klines = [parse_kline(k) for k in raw]

        cur = klines[-1]
        prev = klines[:-1]

        change = calc_price_change_percent(cur["open"], cur["close"])
        spike = calc_volume_spike(
            cur["quote_volume"],
            [k["quote_volume"] for k in prev],
        )

        if cur["quote_volume"] < MIN_QUOTE_VOLUME_5M:
            return None

        if abs(change) < MIN_PRICE_CHANGE_5M:
            return None

        if spike < MIN_VOLUME_SPIKE_RATIO:
            return None

        score = calc_score(change, spike)
        atr = calculate_atr(klines, period=5)

        side = "LONG" if change > 0 else "SHORT"

        return {
            "symbol": symbol,
            "side": side,
            "price_change_5m": change,
            "quote_volume_5m": cur["quote_volume"],
            "volume_spike_ratio": spike,
            "score": score,
            "entry_price": cur["close"],
            "atr": atr,
        }

    except Exception as e:
        logger.warning(f"scan_one failed for {symbol}: {e}")
        return None


async def scan_market():
    watchlist_symbols = get_watchlist_symbols()

    if watchlist_symbols:
        symbols = watchlist_symbols
        logger.info(f"Using watchlist symbols: {symbols}")
    else:
        all_symbols = await get_usdt_symbols()
        symbols = random.sample(all_symbols, min(MAX_SYMBOLS_PER_SCAN, len(all_symbols)))
        logger.info(f"Using random symbols count: {len(symbols)}")

    tasks = [scan_one(s) for s in symbols]
    results = await asyncio.gather(*tasks)

    data = [r for r in results if r]
    data.sort(key=lambda x: x["score"], reverse=True)
    return data[:10]