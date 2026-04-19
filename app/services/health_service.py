import httpx
import logging
from sqlalchemy import text

from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


async def check_binance_api(retries: int = 2) -> bool:
    url = "https://api.binance.com/api/v3/ping"

    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return True

        except Exception as e:
            logger.warning(
                "Binance API check failed (attempt %s/%s): %s",
                attempt + 1,
                retries + 1,
                str(e),
            )

    return False


def check_database() -> bool:
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return True

    except Exception as e:
        logger.error("Database health check failed: %s", str(e))

        try:
            db.rollback()
        except Exception:
            pass

        return False

    finally:
        db.close()
