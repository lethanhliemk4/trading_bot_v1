import time
import hmac
import hashlib
from decimal import Decimal, ROUND_DOWN
from typing import Optional

import httpx

from app.config import get_settings

settings = get_settings()

KLINES_PATH = "/api/v3/klines"
EXCHANGE_INFO_PATH = "/api/v3/exchangeInfo"


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _normalize_symbol(symbol: str) -> str:
    return str(symbol).upper().strip()


def _decimal_from_value(value) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def _floor_to_step(value: float, step: float) -> float:
    value_dec = _decimal_from_value(value)
    step_dec = _decimal_from_value(step)

    if value_dec <= 0 or step_dec <= 0:
        return 0.0

    floored = (value_dec / step_dec).to_integral_value(rounding=ROUND_DOWN) * step_dec
    return float(floored)


def _format_decimal_str(value) -> str:
    dec = _decimal_from_value(value)
    text = format(dec, "f")

    if "." in text:
        text = text.rstrip("0").rstrip(".")

    if text == "" or text == "-0":
        return "0"

    return text


def _stringify_param_value(value):
    if isinstance(value, bool):
        return "true" if value else "false"

    if isinstance(value, (int, str)):
        return str(value)

    if isinstance(value, float):
        return _format_decimal_str(value)

    if isinstance(value, Decimal):
        return _format_decimal_str(value)

    return str(value)


def _prepare_params(params: dict | None) -> dict:
    raw = params or {}
    prepared = {}

    for key, value in raw.items():
        if value is None:
            continue
        prepared[key] = _stringify_param_value(value)

    return prepared


def _get_base_url() -> str:
    return settings.active_binance_rest_base_url


def _get_headers() -> dict:
    headers = {
        "Content-Type": "application/json",
    }

    if settings.BINANCE_API_KEY:
        headers["X-MBX-APIKEY"] = settings.BINANCE_API_KEY

    return headers


def _sign_params(params: dict) -> dict:
    """
    Sign params for Binance private endpoints
    """
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    signature = hmac.new(
        settings.BINANCE_API_SECRET.encode(),
        query_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    params["signature"] = signature
    return params


async def _get(
    path: str,
    params: Optional[dict] = None,
    signed: bool = False,
):
    url = _get_base_url() + path

    params = _prepare_params(params)

    if signed:
        params["timestamp"] = str(int(time.time() * 1000))
        params["recvWindow"] = _stringify_param_value(settings.BINANCE_RECV_WINDOW_MS)
        params = _sign_params(params)

    async with httpx.AsyncClient(timeout=settings.BINANCE_HTTP_TIMEOUT_SECONDS) as client:
        response = await client.get(
            url,
            params=params,
            headers=_get_headers(),
        )
        response.raise_for_status()
        return response.json()


async def _post(
    path: str,
    params: Optional[dict] = None,
    signed: bool = True,
):
    url = _get_base_url() + path

    params = _prepare_params(params)

    if signed:
        params["timestamp"] = str(int(time.time() * 1000))
        params["recvWindow"] = _stringify_param_value(settings.BINANCE_RECV_WINDOW_MS)
        params = _sign_params(params)

    async with httpx.AsyncClient(timeout=settings.BINANCE_HTTP_TIMEOUT_SECONDS) as client:
        response = await client.post(
            url,
            params=params,
            headers=_get_headers(),
        )
        response.raise_for_status()
        return response.json()


async def _delete(
    path: str,
    params: Optional[dict] = None,
    signed: bool = True,
):
    url = _get_base_url() + path

    params = _prepare_params(params)

    if signed:
        params["timestamp"] = str(int(time.time() * 1000))
        params["recvWindow"] = _stringify_param_value(settings.BINANCE_RECV_WINDOW_MS)
        params = _sign_params(params)

    async with httpx.AsyncClient(timeout=settings.BINANCE_HTTP_TIMEOUT_SECONDS) as client:
        response = await client.delete(
            url,
            params=params,
            headers=_get_headers(),
        )
        response.raise_for_status()
        return response.json()


# =========================
# PUBLIC API (giữ nguyên logic cũ)
# =========================
async def get_exchange_info():
    return await _get(EXCHANGE_INFO_PATH)


async def get_usdt_symbols() -> list[str]:
    data = await get_exchange_info()

    symbols = []

    for item in data.get("symbols", []):
        if item.get("status") != "TRADING":
            continue
        if item.get("quoteAsset") != "USDT":
            continue

        symbols.append(item["symbol"])

    return symbols


async def get_klines(symbol: str, interval: str = "5m", limit: int = 6):
    params = {
        "symbol": _normalize_symbol(symbol),
        "interval": interval,
        "limit": limit,
    }

    return await _get(KLINES_PATH, params=params)


async def get_symbol_info(symbol: str) -> dict | None:
    normalized_symbol = _normalize_symbol(symbol)
    data = await get_exchange_info()

    for item in data.get("symbols", []):
        if _normalize_symbol(item.get("symbol", "")) == normalized_symbol:
            return item

    return None


def extract_symbol_filters(symbol_info: dict) -> dict:
    filters = {
        "price_filter": {},
        "lot_size": {},
        "market_lot_size": {},
        "min_notional": {},
        "notional": {},
    }

    for f in symbol_info.get("filters", []):
        filter_type = f.get("filterType")

        if filter_type == "PRICE_FILTER":
            filters["price_filter"] = f
        elif filter_type == "LOT_SIZE":
            filters["lot_size"] = f
        elif filter_type == "MARKET_LOT_SIZE":
            filters["market_lot_size"] = f
        elif filter_type == "MIN_NOTIONAL":
            filters["min_notional"] = f
        elif filter_type == "NOTIONAL":
            filters["notional"] = f

    return filters


async def get_symbol_trading_rules(symbol: str) -> dict | None:
    symbol_info = await get_symbol_info(symbol)
    if not symbol_info:
        return None

    filters = extract_symbol_filters(symbol_info)

    price_filter = filters["price_filter"]
    lot_size = filters["lot_size"]
    market_lot_size = filters["market_lot_size"]
    min_notional = filters["min_notional"]
    notional = filters["notional"]

    min_qty = _safe_float(lot_size.get("minQty"))
    max_qty = _safe_float(lot_size.get("maxQty"))
    step_size = _safe_float(lot_size.get("stepSize"))

    market_min_qty = _safe_float(market_lot_size.get("minQty"))
    market_max_qty = _safe_float(market_lot_size.get("maxQty"))
    market_step_size = _safe_float(market_lot_size.get("stepSize"))

    tick_size = _safe_float(price_filter.get("tickSize"))
    min_price = _safe_float(price_filter.get("minPrice"))
    max_price = _safe_float(price_filter.get("maxPrice"))

    min_notional_value = _safe_float(min_notional.get("minNotional"))
    if min_notional_value <= 0:
        min_notional_value = _safe_float(notional.get("minNotional"))

    max_notional_value = _safe_float(notional.get("maxNotional"))

    return {
        "symbol": _normalize_symbol(symbol_info.get("symbol", symbol)),
        "status": symbol_info.get("status"),
        "base_asset": symbol_info.get("baseAsset"),
        "quote_asset": symbol_info.get("quoteAsset"),
        "tick_size": tick_size,
        "min_price": min_price,
        "max_price": max_price,
        "min_qty": min_qty,
        "max_qty": max_qty,
        "step_size": step_size,
        "market_min_qty": market_min_qty,
        "market_max_qty": market_max_qty,
        "market_step_size": market_step_size,
        "min_notional": min_notional_value,
        "max_notional": max_notional_value,
        "raw_symbol_info": symbol_info,
        "raw_filters": filters,
    }


async def normalize_order_quantity(symbol: str, quantity: float, is_market_order: bool = True) -> dict | None:
    rules = await get_symbol_trading_rules(symbol)
    if not rules:
        return None

    raw_qty = _safe_float(quantity)
    if raw_qty <= 0:
        return {
            "ok": False,
            "reason": "Invalid quantity",
            "symbol": _normalize_symbol(symbol),
            "raw_quantity": raw_qty,
            "normalized_quantity": 0.0,
            "normalized_quantity_str": "0",
            "rules": rules,
        }

    if is_market_order and rules["market_step_size"] > 0:
        step_size = rules["market_step_size"]
        min_qty = rules["market_min_qty"] if rules["market_min_qty"] > 0 else rules["min_qty"]
        max_qty = rules["market_max_qty"] if rules["market_max_qty"] > 0 else rules["max_qty"]
    else:
        step_size = rules["step_size"]
        min_qty = rules["min_qty"]
        max_qty = rules["max_qty"]

    normalized_qty = _floor_to_step(raw_qty, step_size) if step_size > 0 else raw_qty

    if normalized_qty <= 0:
        return {
            "ok": False,
            "reason": "Quantity became zero after step normalization",
            "symbol": _normalize_symbol(symbol),
            "raw_quantity": raw_qty,
            "normalized_quantity": normalized_qty,
            "normalized_quantity_str": _format_decimal_str(normalized_qty),
            "rules": rules,
        }

    if min_qty > 0 and normalized_qty < min_qty:
        return {
            "ok": False,
            "reason": f"Quantity below minQty ({normalized_qty} < {min_qty})",
            "symbol": _normalize_symbol(symbol),
            "raw_quantity": raw_qty,
            "normalized_quantity": normalized_qty,
            "normalized_quantity_str": _format_decimal_str(normalized_qty),
            "rules": rules,
        }

    if max_qty > 0 and normalized_qty > max_qty:
        return {
            "ok": False,
            "reason": f"Quantity above maxQty ({normalized_qty} > {max_qty})",
            "symbol": _normalize_symbol(symbol),
            "raw_quantity": raw_qty,
            "normalized_quantity": normalized_qty,
            "normalized_quantity_str": _format_decimal_str(normalized_qty),
            "rules": rules,
        }

    return {
        "ok": True,
        "reason": None,
        "symbol": _normalize_symbol(symbol),
        "raw_quantity": raw_qty,
        "normalized_quantity": normalized_qty,
        "normalized_quantity_str": _format_decimal_str(normalized_qty),
        "rules": rules,
    }


async def normalize_order_price(symbol: str, price: float) -> dict | None:
    rules = await get_symbol_trading_rules(symbol)
    if not rules:
        return None

    raw_price = _safe_float(price)
    if raw_price <= 0:
        return {
            "ok": False,
            "reason": "Invalid price",
            "symbol": _normalize_symbol(symbol),
            "raw_price": raw_price,
            "normalized_price": 0.0,
            "normalized_price_str": "0",
            "rules": rules,
        }

    tick_size = rules["tick_size"]
    normalized_price = _floor_to_step(raw_price, tick_size) if tick_size > 0 else raw_price

    if normalized_price <= 0:
        return {
            "ok": False,
            "reason": "Price became zero after tick normalization",
            "symbol": _normalize_symbol(symbol),
            "raw_price": raw_price,
            "normalized_price": normalized_price,
            "normalized_price_str": _format_decimal_str(normalized_price),
            "rules": rules,
        }

    if rules["min_price"] > 0 and normalized_price < rules["min_price"]:
        return {
            "ok": False,
            "reason": f"Price below minPrice ({normalized_price} < {rules['min_price']})",
            "symbol": _normalize_symbol(symbol),
            "raw_price": raw_price,
            "normalized_price": normalized_price,
            "normalized_price_str": _format_decimal_str(normalized_price),
            "rules": rules,
        }

    if rules["max_price"] > 0 and normalized_price > rules["max_price"]:
        return {
            "ok": False,
            "reason": f"Price above maxPrice ({normalized_price} > {rules['max_price']})",
            "symbol": _normalize_symbol(symbol),
            "raw_price": raw_price,
            "normalized_price": normalized_price,
            "normalized_price_str": _format_decimal_str(normalized_price),
            "rules": rules,
        }

    return {
        "ok": True,
        "reason": None,
        "symbol": _normalize_symbol(symbol),
        "raw_price": raw_price,
        "normalized_price": normalized_price,
        "normalized_price_str": _format_decimal_str(normalized_price),
        "rules": rules,
    }


async def validate_min_notional(symbol: str, quantity: float, reference_price: float) -> dict | None:
    rules = await get_symbol_trading_rules(symbol)
    if not rules:
        return None

    qty = _safe_float(quantity)
    price = _safe_float(reference_price)
    notional = qty * price
    min_notional = _safe_float(rules.get("min_notional"))

    if qty <= 0 or price <= 0:
        return {
            "ok": False,
            "reason": "Invalid quantity or price for notional check",
            "symbol": _normalize_symbol(symbol),
            "quantity": qty,
            "quantity_str": _format_decimal_str(qty),
            "price": price,
            "price_str": _format_decimal_str(price),
            "notional": notional,
            "min_notional": min_notional,
            "rules": rules,
        }

    if min_notional > 0 and notional < min_notional:
        return {
            "ok": False,
            "reason": f"Notional below minNotional ({notional:.8f} < {min_notional:.8f})",
            "symbol": _normalize_symbol(symbol),
            "quantity": qty,
            "quantity_str": _format_decimal_str(qty),
            "price": price,
            "price_str": _format_decimal_str(price),
            "notional": notional,
            "min_notional": min_notional,
            "rules": rules,
        }

    max_notional = _safe_float(rules.get("max_notional"))
    if max_notional > 0 and notional > max_notional:
        return {
            "ok": False,
            "reason": f"Notional above maxNotional ({notional:.8f} > {max_notional:.8f})",
            "symbol": _normalize_symbol(symbol),
            "quantity": qty,
            "quantity_str": _format_decimal_str(qty),
            "price": price,
            "price_str": _format_decimal_str(price),
            "notional": notional,
            "min_notional": min_notional,
            "max_notional": max_notional,
            "rules": rules,
        }

    return {
        "ok": True,
        "reason": None,
        "symbol": _normalize_symbol(symbol),
        "quantity": qty,
        "quantity_str": _format_decimal_str(qty),
        "price": price,
        "price_str": _format_decimal_str(price),
        "notional": notional,
        "min_notional": min_notional,
        "max_notional": max_notional,
        "rules": rules,
    }


# =========================
# PRIVATE API
# =========================
async def get_account_info():
    return await _get("/api/v3/account", signed=True)


async def get_balance(asset: str = "USDT") -> float:
    data = await get_account_info()

    for b in data.get("balances", []):
        if b["asset"] == asset:
            return float(b["free"])

    return 0.0


async def get_order(symbol: str, order_id: int | str):
    params = {
        "symbol": _normalize_symbol(symbol),
        "orderId": order_id,
    }
    return await _get("/api/v3/order", params=params, signed=True)


async def get_open_orders(symbol: str | None = None):
    params = {}
    if symbol:
        params["symbol"] = _normalize_symbol(symbol)
    return await _get("/api/v3/openOrders", params=params, signed=True)


async def get_all_orders(symbol: str, limit: int = 20):
    params = {
        "symbol": _normalize_symbol(symbol),
        "limit": limit,
    }
    return await _get("/api/v3/allOrders", params=params, signed=True)


async def place_market_order(
    symbol: str,
    side: str,
    quantity: float | str,
):
    """
    side: BUY / SELL
    """
    params = {
        "symbol": _normalize_symbol(symbol),
        "side": side,
        "type": "MARKET",
        "quantity": _format_decimal_str(quantity),
    }

    return await _post("/api/v3/order", params=params)


async def cancel_order(symbol: str, order_id: int):
    params = {
        "symbol": _normalize_symbol(symbol),
        "orderId": order_id,
    }

    return await _delete("/api/v3/order", params=params)