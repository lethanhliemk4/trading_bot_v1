import httpx
from sqlalchemy import text

from app.db.session import SessionLocal


async def check_binance_api() -> bool:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.binance.com/api/v3/ping",
                timeout=10.0,
            )
            response.raise_for_status()
            return True
    except Exception:
        return False


def check_database() -> bool:
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
    finally:
        db.close()