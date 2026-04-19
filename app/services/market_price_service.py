import httpx

BINANCE_PRICE_URL = "https://api.binance.com/api/v3/ticker/price"


async def get_symbol_price(symbol: str) -> float | None:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                BINANCE_PRICE_URL,
                params={"symbol": symbol},
                timeout=15.0,
            )
            response.raise_for_status()
            data = response.json()
            return float(data["price"])
    except Exception:
        return None
