from app.db.session import SessionLocal
from app.db.models import Watchlist


def get_watchlist():
    db = SessionLocal()
    try:
        return db.query(Watchlist).order_by(Watchlist.symbol.asc()).all()
    finally:
        db.close()


def get_watchlist_symbols() -> list[str]:
    db = SessionLocal()
    try:
        items = db.query(Watchlist).order_by(Watchlist.symbol.asc()).all()
        return [item.symbol for item in items]
    finally:
        db.close()


def add_watchlist_symbol(symbol: str) -> bool:
    db = SessionLocal()
    try:
        symbol = symbol.upper().strip()

        exists = db.query(Watchlist).filter(Watchlist.symbol == symbol).first()
        if exists:
            return False

        item = Watchlist(symbol=symbol)
        db.add(item)
        db.commit()
        return True
    finally:
        db.close()


def remove_watchlist_symbol(symbol: str) -> bool:
    db = SessionLocal()
    try:
        symbol = symbol.upper().strip()

        item = db.query(Watchlist).filter(Watchlist.symbol == symbol).first()
        if not item:
            return False

        db.delete(item)
        db.commit()
        return True
    finally:
        db.close()


def clear_watchlist() -> int:
    db = SessionLocal()
    try:
        count = db.query(Watchlist).count()
        db.query(Watchlist).delete()
        db.commit()
        return count
    finally:
        db.close()
