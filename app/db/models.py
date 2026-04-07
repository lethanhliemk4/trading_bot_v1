from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.sql import func

from app.db.session import Base


class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)

    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False, default="LONG")

    score = Column(Float, nullable=False)

    price_change_5m = Column(Float, nullable=False)
    quote_volume_5m = Column(Float, nullable=False)
    volume_spike_ratio = Column(Float, nullable=False)

    entry_price = Column(Float, nullable=False)

    status = Column(String(20), nullable=False, default="pending")

    result_5m = Column(Float, nullable=True)
    result_15m = Column(Float, nullable=True)

    max_profit = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)

    checked_5m_at = Column(DateTime(timezone=True), nullable=True)
    checked_15m_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Watchlist(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BotState(Base):
    __tablename__ = "bot_state"

    id = Column(Integer, primary_key=True, index=True)
    trade_mode = Column(String(20), nullable=False, default="OFF")
    auto_trade_enabled = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PaperTrade(Base):
    __tablename__ = "paper_trades"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)

    entry_price = Column(Float, nullable=False)
    sl = Column(Float, nullable=False)
    tp1 = Column(Float, nullable=False)
    tp2 = Column(Float, nullable=False)
    rr = Column(Float, nullable=False)

    risk_amount = Column(Float, nullable=False)
    position_size = Column(Float, nullable=False)
    notional = Column(Float, nullable=False)

    status = Column(String(20), nullable=False, default="OPEN")
    exit_price = Column(Float, nullable=True)
    result_percent = Column(Float, nullable=True)
    close_reason = Column(String(20), nullable=True)

    tp1_hit = Column(Boolean, default=False)
    tp1_hit_at = Column(DateTime(timezone=True), nullable=True)

    trailing_sl = Column(Float, nullable=True)
    trailing_active = Column(Boolean, default=False)

    tp1_closed_size = Column(Float, default=0.0)
    remaining_size = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)