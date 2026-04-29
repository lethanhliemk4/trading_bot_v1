from fastapi import APIRouter

from app.dashboard.service import get_overview, get_insights


router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/overview")
def overview():
    return get_overview()


@router.get("/insights")
def insights():
    return get_insights()