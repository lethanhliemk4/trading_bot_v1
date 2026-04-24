from fastapi import APIRouter, Query

from app.services.dashboard_service import (
    get_dashboard_overview,
    get_dashboard_live_trades,
    get_dashboard_open_live_trades,
    get_dashboard_signals,
    get_dashboard_risk,
)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/overview")
async def dashboard_overview():
    return await get_dashboard_overview()


@router.get("/live-trades")
def dashboard_live_trades(limit: int = Query(default=50, ge=1, le=200)):
    return get_dashboard_live_trades(limit=limit)


@router.get("/open-live-trades")
def dashboard_open_live_trades():
    return get_dashboard_open_live_trades()


@router.get("/signals")
def dashboard_signals(limit: int = Query(default=50, ge=1, le=200)):
    return get_dashboard_signals(limit=limit)


@router.get("/risk")
def dashboard_risk():
    return get_dashboard_risk()