from app.db.session import SessionLocal
from app.db.models import BotState


VALID_MODES = {"OFF", "PAPER", "LIVE"}


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

        return {
            "trade_mode": state.trade_mode,
            "auto_trade_enabled": state.auto_trade_enabled,
        }
    finally:
        db.close()


def set_trade_mode(mode: str) -> dict:
    mode = mode.upper().strip()
    if mode not in VALID_MODES:
        raise ValueError(f"Invalid mode: {mode}")

    db = SessionLocal()
    try:
        state = db.query(BotState).first()
        if not state:
            state = BotState()
            db.add(state)
            db.commit()
            db.refresh(state)

        state.trade_mode = mode
        state.auto_trade_enabled = mode in {"PAPER", "LIVE"}

        db.commit()
        db.refresh(state)

        return {
            "trade_mode": state.trade_mode,
            "auto_trade_enabled": state.auto_trade_enabled,
        }
    finally:
        db.close()


def panic_stop() -> dict:
    db = SessionLocal()
    try:
        state = db.query(BotState).first()
        if not state:
            state = BotState()
            db.add(state)
            db.commit()
            db.refresh(state)

        state.trade_mode = "OFF"
        state.auto_trade_enabled = False

        db.commit()
        db.refresh(state)

        return {
            "trade_mode": state.trade_mode,
            "auto_trade_enabled": state.auto_trade_enabled,
        }
    finally:
        db.close()