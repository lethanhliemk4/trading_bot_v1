import httpx

BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
BINANCE_EXCHANGE_INFO_URL = "https://api.binance.com/api/v3/exchangeInfo"


async def get_usdt_symbols() -> list[str]:
    async with httpx.AsyncClient() as client:
        response = await client.get(BINANCE_EXCHANGE_INFO_URL, timeout=20.0)
        response.raise_for_status()
        data = response.json()

    symbols = []

    for item in data.get("symbols", []):
        if item.get("status") != "TRADING":
            continue
        if item.get("quoteAsset") != "USDT":
            continue

        symbols.append(item["symbol"])

    return symbols


async def get_klines(symbol: str, interval: str = "5m", limit: int = 6):
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit,
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(BINANCE_KLINES_URL, params=params, timeout=20.0)
        response.raise_for_status()
        return response.json()