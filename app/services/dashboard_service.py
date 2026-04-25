from app.services.trade_mode_service import get_trade_mode
from app.services.risk_service import (
    get_today_live_realized_pnl,
    get_live_risk_summary,
)
from app.services.live_trade_service import (
    get_open_live_trades,
    get_latest_live_trades,
    get_live_trade_stats,
    get_live_account_snapshot,
)
from app.services.signal_service import get_latest_signals


async def get_dashboard_overview() -> dict:
    mode_state = get_trade_mode()
    live_stats = get_live_trade_stats()
    live_risk = get_live_risk_summary()
    account = await get_live_account_snapshot()

    return {
        "bot": {
            "trade_mode": mode_state["trade_mode"],
            "auto_trade_enabled": mode_state["auto_trade_enabled"],
            "app_env": mode_state["app_env"],
            "kill_switch": mode_state["kill_switch"],
            "live_enabled": mode_state["live_enabled"],
        },
        "account": {
            "free_usdt": account["free_usdt"],
            "binance_use_testnet": account["binance_use_testnet"],
            "live_execution_armed": account["live_execution_armed"],
        },
        "live": {
            "total": live_stats["total"],
            "open": live_stats["open"],
            "closed": live_stats["closed"],
            "failed": live_stats["failed"],
            "wins": live_stats["wins"],
            "loses": live_stats["loses"],
            "draws": live_stats["draws"],
            "winrate": live_stats["winrate"],
            "today_pnl": get_today_live_realized_pnl(),
            "tp1_hits": live_stats["tp1_hits"],
        },
        "risk": live_risk,
    }


def get_dashboard_live_trades(limit: int = 50) -> dict:
    trades = get_latest_live_trades(limit=limit)

    return {
        "items": [
            {
                "id": t.id,
                "symbol": t.symbol,
                "side": t.side,
                "status": t.status,
                "environment": t.environment,
                "entry_price": t.entry_price,
                "exit_price": t.exit_price,
                "requested_qty": t.requested_qty,
                "executed_qty": t.executed_qty,
                "remaining_qty": t.remaining_qty,
                "realized_pnl": t.realized_pnl,
                "result_percent": t.result_percent,
                "close_reason": t.close_reason,
                "fail_reason": t.fail_reason,
                "tp1_hit": t.tp1_hit,
                "trailing_active": t.trailing_active,
                "trailing_sl": t.trailing_sl,
                "created_at": str(t.created_at) if t.created_at else None,
                "closed_at": str(t.closed_at) if t.closed_at else None,
            }
            for t in trades
        ]
    }


def get_dashboard_open_live_trades() -> dict:
    trades = get_open_live_trades(limit=50)

    return {
        "items": [
            {
                "id": t.id,
                "symbol": t.symbol,
                "side": t.side,
                "status": t.status,
                "entry_price": t.entry_price,
                "sl": t.sl,
                "tp1": t.tp1,
                "tp2": t.tp2,
                "requested_qty": t.requested_qty,
                "executed_qty": t.executed_qty,
                "remaining_qty": t.remaining_qty,
                "tp1_hit": t.tp1_hit,
                "trailing_active": t.trailing_active,
                "trailing_sl": t.trailing_sl,
                "created_at": str(t.created_at) if t.created_at else None,
            }
            for t in trades
        ]
    }


def get_dashboard_signals(limit: int = 50) -> dict:
    signals = get_latest_signals(limit)

    return {
        "items": [
            {
                "id": s.id,
                "symbol": s.symbol,
                "side": s.side,
                "score": s.score,
                "price_change_5m": s.price_change_5m,
                "quote_volume_5m": s.quote_volume_5m,
                "volume_spike_ratio": s.volume_spike_ratio,
                "entry_price": s.entry_price,
                "status": s.status,
                "result_5m": s.result_5m,
                "result_15m": s.result_15m,
                "max_profit": s.max_profit,
                "max_drawdown": s.max_drawdown,
                "created_at": str(s.created_at) if s.created_at else None,
            }
            for s in signals
        ]
    }


def get_dashboard_risk() -> dict:
    return get_live_risk_summary()

def get_dashboard_runtime() -> dict:
    import time

    import app.main as main_app

    now = time.time()
    threshold = float(main_app.LOOP_STALE_THRESHOLD_SECONDS)

    def build_loop_status(last_seen: float) -> dict:
        last_seen = float(last_seen or 0)

        if last_seen <= 0:
            return {
                "last_seen": None,
                "age_seconds": None,
                "stale": True,
            }

        age = now - last_seen

        return {
            "last_seen": last_seen,
            "age_seconds": round(age, 1),
            "stale": age > threshold,
        }

    return {
        "threshold_seconds": threshold,
        "scanner_loop": build_loop_status(main_app.scanner_loop_last_seen),
        "paper_trade_loop": build_loop_status(main_app.paper_trade_loop_last_seen),
        "live_trade_loop": build_loop_status(main_app.live_trade_loop_last_seen),
        "performance_loop": build_loop_status(main_app.performance_loop_last_seen),
    }