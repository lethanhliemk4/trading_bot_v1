import asyncio
import json
import logging
import websockets

logger = logging.getLogger(__name__)

BINANCE_WS_URL = "wss://stream.binance.com:9443/ws/btcusdt@trade"


async def stream_btc_trades():
    while True:
        try:
            logger.info("Connecting to Binance WebSocket...")

            async with websockets.connect(
                BINANCE_WS_URL,
                ping_interval=20,
                ping_timeout=20,
            ) as ws:
                logger.info("Connected to Binance WebSocket")

                async for message in ws:
                    data = json.loads(message)
                    price = data.get("p")
                    qty = data.get("q")
                    trade_time = data.get("T")

                    logger.info(
                        f"BTCUSDT trade | price={price} qty={qty} time={trade_time}"
                    )

        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            logger.info("Reconnecting in 5 seconds...")
            await asyncio.sleep(5)
