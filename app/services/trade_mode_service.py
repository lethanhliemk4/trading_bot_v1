from app.config import get_settings
from app.db.session import SessionLocal
from app.db.models import BotState

settings = get_settings()

VALID_MODES = {"OFF", "PAPER", "LIVE"}


def _serialize_state(state: BotState) -> dict:
    return {
        "trade_mode": state.trade_mode,
        "auto_trade_enabled": state.auto_trade_enabled,
        "kill_switch": settings.KILL_SWITCH,
        "live_enabled": settings.ENABLE_LIVE_TRADING,
        "app_env": settings.APP_ENV,
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