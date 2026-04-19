from app.config import get_settings
from app.db.session import SessionLocal
from app.db.models import BotState
from app.services.live_trade_service import is_live_execution_armed

settings = get_settings()

VALID_MODES = {"OFF", "PAPER", "LIVE"}


def _safe_live_execution_state() -> tuple[bool, str | None]:
    try:
        result = is_live_execution_armed()

        if isinstance(result, tuple):
            if len(result) >= 2:
                return bool(result[0]), result[1]
            if len(result) == 1:
                return bool(result[0]), None
            return False, "invalid live execution state"

        if isinstance(result, bool):
            return result, None

        if result is None:
            return False, None

        return bool(result), None
    except Exception as e:
        return False, f"live guard error: {e}"


def _serialize_state(state: BotState) -> dict:
    live_execution_armed, live_execution_reason = _safe_live_execution_state()

    return {
        "trade_mode": state.trade_mode,
        "auto_trade_enabled": state.auto_trade_enabled,
        "kill_switch": settings.KILL_SWITCH,
        "live_enabled": settings.ENABLE_LIVE_TRADING,
        "app_env": settings.APP_ENV,
        "app_mode": settings.APP_MODE,
        "binance_use_testnet": settings.BINANCE_USE_TESTNET,
        "live_execution_enabled": settings.LIVE_EXECUTION_ENABLED,
        "live_confirm_real_orders": settings.LIVE_CONFIRM_REAL_ORDERS,
        "live_execution_armed": live_execution_armed,
        "live_execution_reason": live_execution_reason,
    }


def get_or_create_bot_state():
    db = SessionLocal()
    try:
        state = db.query(BotState).first()
        if not state:
            state = BotState(trade_mode="OFF", auto_trade_enabled=False)
            db.add(state)
            db.commit()
            db.refresh(state)
        return state
    finally:
        db.close()


def get_trade_mode() -> dict:
    db = SessionLocal()
    try:
        state = db.query(BotState).first()
        if not state:
            state = BotState(trade_mode="OFF", auto_trade_enabled=False)
            db.add(state)
            db.commit()
            db.refresh(state)

        return _serialize_state(state)
    finally:
        db.close()


def can_enable_paper_mode() -> tuple[bool, str | None]:
    if settings.KILL_SWITCH:
        return False, "KILL_SWITCH is active"

    return True, None


def can_enable_live_mode() -> tuple[bool, str | None]:
    if settings.KILL_SWITCH:
        return False, "KILL_SWITCH is active"

    if settings.REQUIRE_PROD_FOR_LIVE and settings.APP_ENV.lower() != "prod":
        return False, f"LIVE mode requires APP_ENV=prod, current={settings.APP_ENV}"

    if not settings.ENABLE_LIVE_TRADING:
        return False, "ENABLE_LIVE_TRADING is false"

    if not settings.live_allowed_user_id_list:
        return False, "LIVE_ALLOWED_USER_IDS is empty"

    return True, None


def set_trade_mode(mode: str) -> dict:
    mode = mode.upper().strip()
    if mode not in VALID_MODES:
        raise ValueError(f"Invalid mode: {mode}")

    if mode == "PAPER":
        allowed, reason = can_enable_paper_mode()
        if not allowed:
            raise ValueError(reason)

    if mode == "LIVE":
        allowed, reason = can_enable_live_mode()
        if not allowed:
            raise ValueError(reason)

    db = SessionLocal()
    try:
        state = db.query(BotState).first()
        if not state:
            state = BotState(trade_mode="OFF", auto_trade_enabled=False)
            db.add(state)
            db.commit()
            db.refresh(state)

        state.trade_mode = mode
        state.auto_trade_enabled = mode in {"PAPER", "LIVE"}

        db.commit()
        db.refresh(state)

        return _serialize_state(state)
    finally:
        db.close()


def panic_stop() -> dict:
    db = SessionLocal()
    try:
        state = db.query(BotState).first()
        if not state:
            state = BotState(trade_mode="OFF", auto_trade_enabled=False)
            db.add(state)
            db.commit()
            db.refresh(state)

        state.trade_mode = "OFF"
        state.auto_trade_enabled = False

        db.commit()
        db.refresh(state)

        return _serialize_state(state)
    finally:
        db.close()