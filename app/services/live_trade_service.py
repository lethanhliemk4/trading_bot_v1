from datetime import datetime, timezone
import logging
import asyncio

from app.config import get_settings
from app.market.rest_client import (
    get_account_info,
    get_balance,
    get_order,
    place_market_order,
    normalize_order_quantity,
    validate_min_notional,
)
from app.db.session import SessionLocal
from app.db.models import LiveTrade
from app.services.risk_service import validate_live_risk_limits

settings = get_settings()
logger = logging.getLogger(__name__)


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _normalize_symbol(symbol: str) -> str:
    return str(symbol).upper().strip()


def _normalize_side(side: str) -> str:
    value = str(side).upper().strip()
    if value not in {"LONG", "SHORT"}:
        return "LONG"
    return value


def _strategy_side_to_binance_side(side: str) -> str:
    normalized = _normalize_side(side)
    if normalized == "SHORT":
        return "SELL"
    return "BUY"


def _live_side_to_exit_binance_side(side: str) -> str:
    normalized = _normalize_side(side)
    if normalized == "SHORT":
        return "BUY"
    return "SELL"


def _utcnow():
    return datetime.now(timezone.utc)


def _should_retry_exception(exc: Exception) -> bool:
    text = str(exc).lower()

    retry_keywords = [
        "timeout",
        "timed out",
        "temporarily unavailable",
        "connection reset",
        "connection aborted",
        "connection refused",
        "network",
        "server disconnected",
        "502",
        "503",
        "504",
        "429",
    ]

    return any(keyword in text for keyword in retry_keywords)


async def _retry_async(
    func,
    *args,
    retries: int = 2,
    delay_seconds: float = 1.0,
    operation_name: str = "operation",
    **kwargs,
):
    last_error = None

    for attempt in range(retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_error = e

            if attempt >= retries or not _should_retry_exception(e):
                raise

            logger.warning(
                "%s failed (attempt %s/%s): %s | retrying in %.1fs",
                operation_name,
                attempt + 1,
                retries + 1,
                e,
                delay_seconds,
            )
            await asyncio.sleep(delay_seconds)

    raise last_error


def _count_today_live_trades() -> int:
    db = SessionLocal()
    try:
        start_of_day = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        return (
            db.query(LiveTrade)
            .filter(
                LiveTrade.created_at >= start_of_day,
                LiveTrade.status.in_(["OPEN", "CLOSED"]),
            )
            .count()
        )
    finally:
        db.close()


def _get_last_live_trade_time():
    db = SessionLocal()
    try:
        trade = (
            db.query(LiveTrade)
            .filter(LiveTrade.status.in_(["OPEN", "CLOSED"]))
            .order_by(LiveTrade.created_at.desc())
            .first()
        )
        return trade.created_at if trade else None
    finally:
        db.close()


def _validate_runtime_live_guards() -> tuple[bool, str | None]:
    today_count = _count_today_live_trades()
    if today_count >= settings.LIVE_MAX_TRADES_PER_DAY:
        return (
            False,
            f"Daily trade limit reached ({today_count}/{settings.LIVE_MAX_TRADES_PER_DAY})",
        )

    last_trade_time = _get_last_live_trade_time()
    if last_trade_time:
        if last_trade_time.tzinfo is None:
            last_trade_time = last_trade_time.replace(tzinfo=timezone.utc)

        now_utc = datetime.now(timezone.utc)
        seconds_since_last = (now_utc - last_trade_time).total_seconds()

        if seconds_since_last < 0:
            logger.warning(
                "Runtime guard cooldown anomaly detected | last_trade_time=%s | now=%s | seconds_since_last=%.2f | ignoring cooldown once",
                last_trade_time,
                now_utc,
                seconds_since_last,
            )
            seconds_since_last = settings.LIVE_TRADE_COOLDOWN_SECONDS + 1

        if seconds_since_last < settings.LIVE_TRADE_COOLDOWN_SECONDS:
            return False, (
                f"Cooldown active ({int(seconds_since_last)}s < "
                f"{settings.LIVE_TRADE_COOLDOWN_SECONDS}s)"
            )

    return True, None


def is_live_execution_armed() -> tuple[bool, str | None]:
    if settings.KILL_SWITCH:
        return False, "KILL_SWITCH active"

    if not settings.ENABLE_LIVE_TRADING:
        return False, "ENABLE_LIVE_TRADING is false"

    if not settings.LIVE_EXECUTION_ENABLED:
        return False, "LIVE_EXECUTION_ENABLED is false"

    if not settings.BINANCE_USE_TESTNET:
        if not settings.LIVE_CONFIRM_REAL_ORDERS:
            return False, "LIVE_CONFIRM_REAL_ORDERS is false"

    if settings.REQUIRE_PROD_FOR_LIVE and not settings.is_production:
        return False, "LIVE trading requires APP_ENV=prod"

    if not settings.BINANCE_API_KEY or not settings.BINANCE_API_KEY.strip():
        return False, "Missing BINANCE_API_KEY"

    if not settings.BINANCE_API_SECRET or not settings.BINANCE_API_SECRET.strip():
        return False, "Missing BINANCE_API_SECRET"

    return True, None


def validate_live_inputs(strategy: dict, risk: dict) -> tuple[bool, str | None]:
    try:
        symbol = _normalize_symbol(strategy["symbol"])
        side = _normalize_side(strategy["side"])
        entry = _safe_float(strategy["entry"])
        sl = _safe_float(strategy["sl"])
        tp1 = _safe_float(strategy["tp1"])
        tp2 = _safe_float(strategy["tp2"])

        risk_amount = _safe_float(risk["risk_amount"])
        position_size = _safe_float(risk["position_size"])
        notional = _safe_float(risk["notional"])
    except Exception:
        return False, "Invalid live payload"

    if not symbol:
        return False, "Missing symbol"

    if side not in {"LONG", "SHORT"}:
        return False, "Invalid side"

    if entry <= 0 or sl <= 0 or tp1 <= 0 or tp2 <= 0:
        return False, "Invalid strategy price"

    if risk_amount <= 0:
        return False, "Invalid risk_amount"

    if position_size <= 0:
        return False, "Invalid position_size"

    if notional <= 0:
        return False, "Invalid notional"

    if notional > settings.LIVE_MAX_NOTIONAL_PER_TRADE:
        return False, f"Live notional too high ({notional:.2f})"

    if side == "LONG":
        if sl >= entry:
            return False, "SL must be below entry for LONG"
        if tp1 <= entry or tp2 <= entry:
            return False, "TP1/TP2 must be above entry for LONG"
    else:
        if sl <= entry:
            return False, "SL must be above entry for SHORT"
        if tp1 >= entry or tp2 >= entry:
            return False, "TP1/TP2 must be below entry for SHORT"

    return True, None


async def validate_live_balance(
    required_notional: float,
) -> tuple[bool, str | None, dict]:
    free_usdt = await get_balance("USDT")

    if free_usdt < settings.LIVE_MIN_FREE_USDT:
        return (
            False,
            f"Free USDT below minimum ({free_usdt:.2f} < {settings.LIVE_MIN_FREE_USDT:.2f})",
            {
                "free_usdt": free_usdt,
                "required_notional": required_notional,
            },
        )

    if required_notional > free_usdt:
        return (
            False,
            f"Insufficient free USDT ({free_usdt:.2f} < {required_notional:.2f})",
            {
                "free_usdt": free_usdt,
                "required_notional": required_notional,
            },
        )

    return (
        True,
        None,
        {
            "free_usdt": free_usdt,
            "required_notional": required_notional,
        },
    )


async def get_live_account_snapshot() -> dict:
    account = await get_account_info()
    free_usdt = await get_balance("USDT")

    return {
        "account": account,
        "free_usdt": free_usdt,
        "rest_base_url": settings.active_binance_rest_base_url,
        "ws_base_url": settings.active_binance_ws_base_url,
        "binance_use_testnet": bool(settings.BINANCE_USE_TESTNET),
        "live_execution_armed": bool(settings.is_live_trading_active),
    }


async def build_live_order_preview(strategy: dict, risk: dict) -> dict:
    armed, armed_reason = is_live_execution_armed()
    valid, valid_reason = validate_live_inputs(strategy, risk)

    symbol = _normalize_symbol(strategy.get("symbol", ""))
    side = _normalize_side(strategy.get("side", "LONG"))
    entry = _safe_float(strategy.get("entry"))
    sl = _safe_float(strategy.get("sl"))
    tp1 = _safe_float(strategy.get("tp1"))
    tp2 = _safe_float(strategy.get("tp2"))
    raw_position_size = _safe_float(risk.get("position_size"))
    notional = _safe_float(risk.get("notional"))
    risk_amount = _safe_float(risk.get("risk_amount"))

    normalized_ok = False
    normalized_reason = None
    normalized_qty = 0.0
    normalized_qty_str = "0"

    if valid:
        try:
            normalized = await normalize_order_quantity(symbol, raw_position_size)
            if normalized and normalized.get("ok"):
                normalized_ok = True
                normalized_qty = _safe_float(normalized.get("normalized_quantity"))
                normalized_qty_str = str(normalized.get("normalized_quantity_str", "0"))
            else:
                normalized_reason = (
                    normalized.get("reason")
                    if normalized
                    else "normalize quantity failed"
                )
        except Exception as e:
            normalized_reason = f"Quantity normalization failed: {e}"

    notional_ok = False
    notional_reason = None
    calculated_notional = (
        normalized_qty * entry if normalized_qty > 0 and entry > 0 else 0.0
    )

    if valid and normalized_ok:
        try:
            notional_check = await validate_min_notional(symbol, normalized_qty, entry)
            if notional_check and notional_check.get("ok"):
                notional_ok = True
                calculated_notional = _safe_float(notional_check.get("notional"))
            else:
                notional_reason = (
                    notional_check.get("reason")
                    if notional_check
                    else "min notional validation failed"
                )
        except Exception as e:
            notional_reason = f"Notional validation failed: {e}"

    balance_ok = False
    balance_reason = None
    balance_info = {
        "free_usdt": 0.0,
        "required_notional": (
            calculated_notional if calculated_notional > 0 else notional
        ),
    }

    if valid and normalized_ok and notional_ok:
        try:
            balance_ok, balance_reason, balance_info = await validate_live_balance(
                calculated_notional
            )
        except Exception as e:
            balance_reason = f"Balance check failed: {e}"

    reason = (
        armed_reason
        or valid_reason
        or normalized_reason
        or notional_reason
        or balance_reason
    )

    return {
        "ok": armed and valid and normalized_ok and notional_ok and balance_ok,
        "armed": armed,
        "armed_reason": armed_reason,
        "valid": valid,
        "valid_reason": valid_reason,
        "normalized_ok": normalized_ok,
        "normalized_reason": normalized_reason,
        "notional_ok": notional_ok,
        "notional_reason": notional_reason,
        "balance_ok": balance_ok,
        "balance_reason": balance_reason,
        "reason": reason,
        "symbol": symbol,
        "strategy_side": side,
        "binance_side": _strategy_side_to_binance_side(side),
        "entry": entry,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,
        "raw_position_size": raw_position_size,
        "normalized_qty": normalized_qty,
        "normalized_qty_str": normalized_qty_str,
        "notional": notional,
        "calculated_notional": calculated_notional,
        "risk_amount": risk_amount,
        "free_usdt": _safe_float(balance_info.get("free_usdt")),
        "required_notional": _safe_float(balance_info.get("required_notional")),
        "binance_use_testnet": bool(settings.BINANCE_USE_TESTNET),
        "rest_base_url": settings.active_binance_rest_base_url,
    }


def save_live_trade(
    strategy: dict,
    risk: dict,
    order_response: dict | None,
    status: str,
    fail_reason: str | None = None,
    requested_qty: float | None = None,
):
    db = SessionLocal()
    try:
        now = _utcnow()
        executed_qty = _safe_float((order_response or {}).get("executedQty", 0))
        final_requested_qty = (
            _safe_float(requested_qty)
            if requested_qty is not None
            else _safe_float(risk.get("position_size"))
        )
        remaining_qty = max(final_requested_qty - executed_qty, 0.0)

        order_status = (
            str((order_response or {}).get("status")) if order_response else None
        )
        entry_submitted_at = now if order_response else None
        entry_filled_at = now if executed_qty > 0 else None

        trade = LiveTrade(
            symbol=_normalize_symbol(strategy["symbol"]),
            side=_normalize_side(strategy["side"]),
            environment="testnet" if settings.BINANCE_USE_TESTNET else "mainnet",
            exchange="BINANCE",
            entry_price=_safe_float(strategy["entry"]),
            sl=_safe_float(strategy["sl"]),
            tp1=_safe_float(strategy["tp1"]),
            tp2=_safe_float(strategy["tp2"]),
            rr=_safe_float(strategy.get("rr", 0)),
            risk_amount=_safe_float(risk["risk_amount"]),
            position_size=_safe_float(risk["position_size"]),
            notional=_safe_float(risk["notional"]),
            requested_qty=final_requested_qty,
            executed_qty=executed_qty,
            remaining_qty=remaining_qty,
            avg_fill_price=_safe_float((order_response or {}).get("avgPrice", 0)),
            entry_order_id=(
                str((order_response or {}).get("orderId")) if order_response else None
            ),
            entry_client_order_id=(
                str((order_response or {}).get("clientOrderId"))
                if order_response
                else None
            ),
            entry_order_status=order_status,
            status=status,
            fail_reason=fail_reason,
            raw_order_response=str(order_response)[:5000] if order_response else None,
            opened_at=now if order_response else None,
            entry_submitted_at=entry_submitted_at,
            entry_filled_at=entry_filled_at,
            last_synced_at=now if order_response else None,
        )

        db.add(trade)
        db.commit()
        db.refresh(trade)
        return trade

    finally:
        db.close()


def has_open_live_trade(symbol: str) -> bool:
    db = SessionLocal()
    try:
        trade = (
            db.query(LiveTrade)
            .filter(
                LiveTrade.status == "OPEN",
                LiveTrade.symbol == _normalize_symbol(symbol),
            )
            .first()
        )
        return trade is not None
    finally:
        db.close()


def get_live_trade_by_id(trade_id: int):
    db = SessionLocal()
    try:
        return db.query(LiveTrade).filter(LiveTrade.id == trade_id).first()
    finally:
        db.close()


def get_open_live_trades(limit: int = 20):
    db = SessionLocal()
    try:
        return (
            db.query(LiveTrade)
            .filter(LiveTrade.status == "OPEN")
            .order_by(LiveTrade.created_at.desc())
            .limit(limit)
            .all()
        )
    finally:
        db.close()


def get_all_open_live_trades():
    db = SessionLocal()
    try:
        return (
            db.query(LiveTrade)
            .filter(LiveTrade.status == "OPEN")
            .order_by(LiveTrade.created_at.desc())
            .all()
        )
    finally:
        db.close()


def get_latest_live_trades(limit: int = 20):
    db = SessionLocal()
    try:
        return (
            db.query(LiveTrade).order_by(LiveTrade.created_at.desc()).limit(limit).all()
        )
    finally:
        db.close()


def mark_live_trade_tp1_hit(trade_id: int):
    db = SessionLocal()
    try:
        trade = db.query(LiveTrade).filter(LiveTrade.id == trade_id).first()
        if not trade:
            return None

        if trade.tp1_hit:
            return trade

        trade.tp1_hit = True
        trade.tp1_hit_at = _utcnow()
        trade.last_synced_at = _utcnow()

        db.commit()
        db.refresh(trade)
        return trade
    finally:
        db.close()


def activate_live_trade_trailing(trade_id: int, trailing_sl: float):
    db = SessionLocal()
    try:
        trade = db.query(LiveTrade).filter(LiveTrade.id == trade_id).first()
        if not trade or trade.status != "OPEN":
            return None

        trailing_sl = _safe_float(trailing_sl)
        if trailing_sl <= 0:
            return None

        trade.trailing_active = True
        trade.trailing_sl = trailing_sl
        trade.last_synced_at = _utcnow()

        db.commit()
        db.refresh(trade)
        return trade
    finally:
        db.close()


def update_live_trade_trailing_sl(trade_id: int, trailing_sl: float):
    db = SessionLocal()
    try:
        trade = db.query(LiveTrade).filter(LiveTrade.id == trade_id).first()
        if not trade or trade.status != "OPEN" or not trade.trailing_active:
            return None

        trailing_sl = _safe_float(trailing_sl)
        if trailing_sl <= 0:
            return None

        trade.trailing_sl = trailing_sl
        trade.last_synced_at = _utcnow()

        db.commit()
        db.refresh(trade)
        return trade
    finally:
        db.close()


def close_live_trade(
    trade_id: int,
    exit_price: float,
    result_percent: float,
    close_reason: str,
    exit_order_id: str | None = None,
    exit_order_status: str | None = None,
):
    db = SessionLocal()
    try:
        trade = db.query(LiveTrade).filter(LiveTrade.id == trade_id).first()
        if not trade or trade.status != "OPEN":
            return None

        exit_price = _safe_float(exit_price)
        result_percent = _safe_float(result_percent)

        if exit_price <= 0:
            return None

        size = (
            trade.remaining_qty
            if trade.remaining_qty is not None
            else trade.executed_qty
        )
        if size is None or size <= 0:
            size = trade.executed_qty

        if size is None or size <= 0:
            return None

        if trade.side == "LONG":
            pnl = size * (exit_price - trade.entry_price)
        else:
            pnl = size * (trade.entry_price - exit_price)

        trade.realized_pnl = (trade.realized_pnl or 0.0) + pnl
        trade.exit_price = exit_price
        trade.result_percent = result_percent
        trade.close_reason = close_reason
        trade.exit_order_id = exit_order_id
        trade.exit_order_status = exit_order_status
        trade.status = "CLOSED"
        trade.remaining_qty = 0.0
        trade.closed_at = _utcnow()
        trade.last_synced_at = _utcnow()

        db.commit()
        db.refresh(trade)
        return trade
    finally:
        db.close()


def get_live_trade_stats() -> dict:
    db = SessionLocal()
    try:
        trades = db.query(LiveTrade).all()

        total = len(trades)
        open_count = len([t for t in trades if t.status == "OPEN"])
        closed_trades = [t for t in trades if t.status == "CLOSED"]
        failed_trades = [t for t in trades if t.status == "FAILED"]
        closed_count = len(closed_trades)

        wins = len([t for t in closed_trades if (t.realized_pnl or 0.0) > 0])
        loses = len([t for t in closed_trades if (t.realized_pnl or 0.0) < 0])
        draws = len([t for t in closed_trades if (t.realized_pnl or 0.0) == 0])

        winrate = (wins / closed_count * 100) if closed_count else 0.0

        realized_list = [t.realized_pnl or 0.0 for t in closed_trades]
        avg_result = (sum(realized_list) / len(realized_list)) if realized_list else 0.0
        best_result = max(realized_list) if realized_list else 0.0
        worst_result = min(realized_list) if realized_list else 0.0
        tp1_hits = len([t for t in trades if t.tp1_hit])

        return {
            "total": total,
            "open": open_count,
            "closed": closed_count,
            "failed": len(failed_trades),
            "wins": wins,
            "loses": loses,
            "draws": draws,
            "winrate": winrate,
            "avg_result": avg_result,
            "best_result": best_result,
            "worst_result": worst_result,
            "tp1_hits": tp1_hits,
        }
    finally:
        db.close()


def _sync_live_trade_order_data(trade: LiveTrade, order_data: dict):
    executed_qty = _safe_float(order_data.get("executedQty"), trade.executed_qty or 0.0)
    avg_fill_price = _safe_float(
        order_data.get("avgPrice"), trade.avg_fill_price or 0.0
    )

    if avg_fill_price <= 0:
        cummulative_quote_qty = _safe_float(order_data.get("cummulativeQuoteQty"), 0.0)
        if executed_qty > 0 and cummulative_quote_qty > 0:
            avg_fill_price = cummulative_quote_qty / executed_qty

    trade.entry_order_status = str(
        order_data.get("status", trade.entry_order_status or "")
    )
    trade.executed_qty = executed_qty
    trade.avg_fill_price = (
        avg_fill_price if avg_fill_price > 0 else trade.avg_fill_price
    )

    requested_qty = _safe_float(trade.requested_qty, 0.0)
    if requested_qty > 0:
        trade.remaining_qty = max(requested_qty - executed_qty, 0.0)

    if executed_qty > 0 and trade.entry_filled_at is None:
        trade.entry_filled_at = _utcnow()

    if trade.entry_submitted_at is None:
        trade.entry_submitted_at = _utcnow()

    trade.last_synced_at = _utcnow()


async def sync_live_trade_order(trade_id: int):
    db = SessionLocal()
    try:
        trade = db.query(LiveTrade).filter(LiveTrade.id == trade_id).first()
        if not trade:
            return None

        if not trade.entry_order_id:
            return trade

        try:
            order_data = await _retry_async(
                get_order,
                trade.symbol,
                trade.entry_order_id,
                retries=2,
                delay_seconds=1.0,
                operation_name="sync_live_trade_order.get_order",
            )
        except Exception as e:
            trade.fail_reason = f"sync error: {e}"
            trade.last_synced_at = _utcnow()
            db.commit()
            db.refresh(trade)
            return trade

        _sync_live_trade_order_data(trade, order_data)

        db.commit()
        db.refresh(trade)
        return trade
    finally:
        db.close()


async def sync_open_live_trades():
    db = SessionLocal()
    try:
        trades = (
            db.query(LiveTrade)
            .filter(LiveTrade.status == "OPEN")
            .order_by(LiveTrade.created_at.desc())
            .all()
        )

        updated_ids = []

        for trade in trades:
            if not trade.entry_order_id:
                continue

            try:
                order_data = await _retry_async(
                    get_order,
                    trade.symbol,
                    trade.entry_order_id,
                    retries=2,
                    delay_seconds=1.0,
                    operation_name="sync_open_live_trades.get_order",
                )
            except Exception as e:
                trade.fail_reason = f"sync error: {e}"
                trade.last_synced_at = _utcnow()
                continue

            _sync_live_trade_order_data(trade, order_data)
            updated_ids.append(trade.id)

        db.commit()
        return updated_ids
    finally:
        db.close()


async def execute_live_market_order(strategy: dict, risk: dict) -> dict:
    armed, armed_reason = is_live_execution_armed()
    if not armed:
        return {
            "ok": False,
            "stage": "arming",
            "reason": armed_reason,
            "symbol": _normalize_symbol(strategy.get("symbol", "")),
        }

    runtime_ok, runtime_reason = _validate_runtime_live_guards()
    if not runtime_ok:
        return {
            "ok": False,
            "stage": "runtime_guard",
            "reason": runtime_reason,
            "symbol": _normalize_symbol(strategy.get("symbol", "")),
        }

    valid, valid_reason = validate_live_inputs(strategy, risk)
    if not valid:
        return {
            "ok": False,
            "stage": "validation",
            "reason": valid_reason,
            "symbol": _normalize_symbol(strategy.get("symbol", "")),
        }

    symbol = _normalize_symbol(strategy["symbol"])
    side = _normalize_side(strategy["side"])
    binance_side = _strategy_side_to_binance_side(side)

    if has_open_live_trade(symbol):
        return {
            "ok": False,
            "stage": "duplicate",
            "reason": f"Duplicate live trade blocked for {symbol}",
            "symbol": symbol,
        }

    raw_qty = _safe_float(risk["position_size"])
    entry = _safe_float(strategy["entry"])
    risk_amount = _safe_float(risk["risk_amount"])

    normalized = await normalize_order_quantity(symbol, raw_qty)
    if not normalized:
        save_live_trade(
            strategy,
            risk,
            None,
            "FAILED",
            "normalize quantity failed",
            requested_qty=raw_qty,
        )
        return {
            "ok": False,
            "stage": "quantity",
            "reason": "normalize quantity failed",
            "symbol": symbol,
        }

    if not normalized.get("ok"):
        save_live_trade(
            strategy,
            risk,
            None,
            "FAILED",
            normalized.get("reason"),
            requested_qty=raw_qty,
        )
        return {
            "ok": False,
            "stage": "quantity",
            "reason": normalized.get("reason"),
            "symbol": symbol,
        }

    qty = _safe_float(normalized.get("normalized_quantity"))
    qty_str = str(normalized.get("normalized_quantity_str", "0"))

    if qty <= 0:
        save_live_trade(
            strategy,
            risk,
            None,
            "FAILED",
            "normalized quantity invalid",
            requested_qty=raw_qty,
        )
        return {
            "ok": False,
            "stage": "quantity",
            "reason": "normalized quantity invalid",
            "symbol": symbol,
        }

    notional_check = await validate_min_notional(symbol, qty, entry)
    if not notional_check:
        save_live_trade(
            strategy,
            risk,
            None,
            "FAILED",
            "min notional validation failed",
            requested_qty=qty,
        )
        return {
            "ok": False,
            "stage": "notional",
            "reason": "min notional validation failed",
            "symbol": symbol,
        }

    if not notional_check.get("ok"):
        save_live_trade(
            strategy,
            risk,
            None,
            "FAILED",
            notional_check.get("reason"),
            requested_qty=qty,
        )
        return {
            "ok": False,
            "stage": "notional",
            "reason": notional_check.get("reason"),
            "symbol": symbol,
        }

    required_notional = _safe_float(notional_check.get("notional"), qty * entry)

    live_risk_ok, live_risk_reason = validate_live_risk_limits(
        symbol=symbol,
        notional=required_notional,
        risk_amount=risk_amount,
    )
    if not live_risk_ok:
        return {
            "ok": False,
            "stage": "live_risk",
            "reason": live_risk_reason,
            "symbol": symbol,
            "required_notional": required_notional,
        }

    balance_ok, balance_reason, balance_info = await validate_live_balance(
        required_notional
    )
    if not balance_ok:
        save_live_trade(
            strategy,
            risk,
            None,
            "FAILED",
            balance_reason,
            requested_qty=qty,
        )
        return {
            "ok": False,
            "stage": "balance",
            "reason": balance_reason,
            "symbol": symbol,
            "free_usdt": _safe_float(balance_info.get("free_usdt")),
            "required_notional": _safe_float(balance_info.get("required_notional")),
        }

    logger.warning(
        "[LIVE EXECUTION] %s %s | qty=%s | notional=%.2f",
        symbol,
        binance_side,
        qty_str,
        required_notional,
    )

    try:
        order = await _retry_async(
            place_market_order,
            symbol=symbol,
            side=binance_side,
            quantity=qty_str,
            retries=2,
            delay_seconds=1.0,
            operation_name="execute_live_market_order.place_market_order",
        )
    except Exception as e:
        save_live_trade(
            strategy,
            risk,
            None,
            "FAILED",
            str(e),
            requested_qty=qty,
        )
        return {
            "ok": False,
            "stage": "order",
            "reason": str(e),
            "symbol": symbol,
            "qty": qty,
            "qty_str": qty_str,
        }

    trade = save_live_trade(
        strategy,
        risk,
        order,
        "OPEN",
        requested_qty=qty,
    )

    try:
        if trade and trade.entry_order_id:
            order_data = await _retry_async(
                get_order,
                symbol,
                trade.entry_order_id,
                retries=2,
                delay_seconds=1.0,
                operation_name="execute_live_market_order.post_order_sync",
            )
            db = SessionLocal()
            try:
                db_trade = db.query(LiveTrade).filter(LiveTrade.id == trade.id).first()
                if db_trade:
                    _sync_live_trade_order_data(db_trade, order_data)
                    db.commit()
                    db.refresh(db_trade)
            finally:
                db.close()
    except Exception as e:
        logger.warning("Post-order sync failed for %s: %s", symbol, e)

    return {
        "ok": True,
        "stage": "submitted",
        "reason": None,
        "symbol": symbol,
        "strategy_side": side,
        "binance_side": binance_side,
        "qty": qty,
        "qty_str": qty_str,
        "raw_qty": raw_qty,
        "required_notional": required_notional,
        "binance_use_testnet": bool(settings.BINANCE_USE_TESTNET),
        "order": order,
    }


async def execute_live_close_market_order(trade_id: int) -> dict:
    armed, armed_reason = is_live_execution_armed()
    if not armed:
        return {
            "ok": False,
            "stage": "arming",
            "reason": armed_reason,
            "trade_id": trade_id,
        }

    db = SessionLocal()
    try:
        trade = db.query(LiveTrade).filter(LiveTrade.id == trade_id).first()
        if not trade:
            return {
                "ok": False,
                "stage": "lookup",
                "reason": "Live trade not found",
                "trade_id": trade_id,
            }

        if trade.status != "OPEN":
            return {
                "ok": False,
                "stage": "lookup",
                "reason": f"Trade is not OPEN ({trade.status})",
                "trade_id": trade_id,
                "symbol": trade.symbol,
            }

        if trade.entry_order_id:
            try:
                order_data = await _retry_async(
                    get_order,
                    trade.symbol,
                    trade.entry_order_id,
                    retries=2,
                    delay_seconds=1.0,
                    operation_name="execute_live_close_market_order.pre_close_sync",
                )
                _sync_live_trade_order_data(trade, order_data)
                db.commit()
                db.refresh(trade)
            except Exception as e:
                trade.fail_reason = f"pre-close sync error: {e}"
                trade.last_synced_at = _utcnow()
                db.commit()
                db.refresh(trade)

        symbol = _normalize_symbol(trade.symbol)
        exit_side = _live_side_to_exit_binance_side(trade.side)

        raw_qty = _safe_float(trade.remaining_qty)
        if raw_qty <= 0:
            raw_qty = _safe_float(trade.executed_qty)

        if raw_qty <= 0:
            return {
                "ok": False,
                "stage": "quantity",
                "reason": "No remaining quantity to close",
                "trade_id": trade_id,
                "symbol": symbol,
            }

        normalized = await normalize_order_quantity(symbol, raw_qty)
        if not normalized:
            return {
                "ok": False,
                "stage": "quantity",
                "reason": "normalize quantity failed",
                "trade_id": trade_id,
                "symbol": symbol,
            }

        if not normalized.get("ok"):
            return {
                "ok": False,
                "stage": "quantity",
                "reason": normalized.get("reason"),
                "trade_id": trade_id,
                "symbol": symbol,
            }

        qty = _safe_float(normalized.get("normalized_quantity"))
        qty_str = str(normalized.get("normalized_quantity_str", "0"))

        if qty <= 0:
            return {
                "ok": False,
                "stage": "quantity",
                "reason": "normalized quantity invalid",
                "trade_id": trade_id,
                "symbol": symbol,
            }

        try:
            exit_order = await _retry_async(
                place_market_order,
                symbol=symbol,
                side=exit_side,
                quantity=qty_str,
                retries=2,
                delay_seconds=1.0,
                operation_name="execute_live_close_market_order.place_market_order",
            )
        except Exception as e:
            trade.fail_reason = f"close order error: {e}"
            trade.last_synced_at = _utcnow()
            db.commit()
            db.refresh(trade)
            return {
                "ok": False,
                "stage": "order",
                "reason": str(e),
                "trade_id": trade_id,
                "symbol": symbol,
                "qty": qty,
                "qty_str": qty_str,
            }

        executed_qty = _safe_float(exit_order.get("executedQty"), qty)
        avg_exit_price = _safe_float(exit_order.get("avgPrice"), 0.0)

        if avg_exit_price <= 0:
            cummulative_quote_qty = _safe_float(
                exit_order.get("cummulativeQuoteQty"), 0.0
            )
            if executed_qty > 0 and cummulative_quote_qty > 0:
                avg_exit_price = cummulative_quote_qty / executed_qty

        if avg_exit_price <= 0:
            avg_exit_price = _safe_float(trade.avg_fill_price, trade.entry_price)

        entry_price = _safe_float(trade.avg_fill_price)
        if entry_price <= 0:
            entry_price = _safe_float(trade.entry_price)

        if entry_price <= 0:
            entry_price = 1.0

        if trade.side == "LONG":
            realized_pnl = executed_qty * (avg_exit_price - entry_price)
            result_percent = ((avg_exit_price - entry_price) / entry_price) * 100
        else:
            realized_pnl = executed_qty * (entry_price - avg_exit_price)
            result_percent = ((entry_price - avg_exit_price) / entry_price) * 100

        trade.realized_pnl = (trade.realized_pnl or 0.0) + realized_pnl
        trade.exit_price = avg_exit_price
        trade.result_percent = result_percent
        trade.close_reason = "MANUAL_EXIT"
        trade.exit_order_id = (
            str(exit_order.get("orderId"))
            if exit_order.get("orderId") is not None
            else None
        )
        trade.exit_order_status = (
            str(exit_order.get("status"))
            if exit_order.get("status") is not None
            else None
        )
        trade.status = "CLOSED"
        trade.remaining_qty = 0.0
        trade.closed_at = _utcnow()
        trade.last_synced_at = _utcnow()

        db.commit()
        db.refresh(trade)

        return {
            "ok": True,
            "stage": "submitted",
            "reason": None,
            "trade_id": trade.id,
            "symbol": trade.symbol,
            "exit_side": exit_side,
            "qty": qty,
            "qty_str": qty_str,
            "executed_qty": executed_qty,
            "exit_price": avg_exit_price,
            "result_percent": result_percent,
            "realized_pnl": realized_pnl,
            "binance_use_testnet": bool(settings.BINANCE_USE_TESTNET),
            "order": exit_order,
        }
    finally:
        db.close()