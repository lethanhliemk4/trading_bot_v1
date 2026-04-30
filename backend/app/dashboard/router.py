from fastapi import APIRouter

from app.dashboard.service import (
    get_overview,
    get_insights,
    get_failed_live_trades,
    get_trading_summary,
)


router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/overview")
def overview():
    return get_overview()


@router.get("/insights")
def insights():
    return get_insights()


@router.get("/live-trades/errors")
def failed_live_trades():
    return get_failed_live_trades()


@router.get("/trading-summary")
def trading_summary():
    return get_trading_summary()