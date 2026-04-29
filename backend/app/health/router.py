from fastapi import APIRouter

from app.core.config import settings
from app.db.session import check_database_connection


router = APIRouter(prefix="/api/health", tags=["Health"])


@router.get("")
def health_check():
    db_ok = check_database_connection()

    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "env": settings.APP_ENV,
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
    }