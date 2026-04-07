from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "trading_bot_v1"
    APP_ENV: Literal["dev", "staging", "prod"] = "dev"
    APP_MODE: Literal["test", "prod"] = "prod"
    APP_VERSION: str = "1.0.0"

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_JSON: bool = False

    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_ALLOWED_USER_IDS: str
    LIVE_ALLOWED_USER_IDS: str

    GEMINI_API_KEY: str | None = None

    DB_HOST: str = "mysql"
    DB_PORT: int = 3306
    DB_NAME: str = "binance_bot"
    DB_USER: str = "botuser"
    DB_PASSWORD: str

    ENABLE_LIVE_TRADING: bool = False
    REQUIRE_PROD_FOR_LIVE: bool = True
    KILL_SWITCH: bool = False

    RISK_CAPITAL_USDT: float = 10.0
    RISK_PER_TRADE_PERCENT: float = 1.0

    MAX_OPEN_TRADES: int = 5
    DAILY_LOSS_LIMIT_USDT: float = 100.0
    MAX_NOTIONAL_PER_TRADE: float = 250.0

    SCAN_INTERVAL_SECONDS: int = 30
    PERFORMANCE_CHECK_INTERVAL_SECONDS: int = 60
    PAPER_TRADE_CHECK_INTERVAL_SECONDS: int = 20
    ALERT_COOLDOWN_SECONDS: int = 900

    # ===== Scanner config =====
    SCANNER_MAX_SYMBOLS_PER_SCAN: int = 80
    SCANNER_RESULTS_LIMIT: int = 10
    SCANNER_MIN_QUOTE_VOLUME_5M: float = 50000.0
    SCANNER_MIN_PRICE_CHANGE_5M: float = 0.1
    SCANNER_MIN_VOLUME_SPIKE_RATIO: float = 1.2

    # ===== Test mode config =====
    TEST_MODE_COOLDOWN_SECONDS: int = 10

    @property
    def sqlalchemy_database_uri(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def telegram_allowed_user_id_list(self) -> list[int]:
        return [
            int(x.strip())
            for x in self.TELEGRAM_ALLOWED_USER_IDS.split(",")
            if x.strip()
        ]

    @property
    def live_allowed_user_id_list(self) -> list[int]:
        return [
            int(x.strip())
            for x in self.LIVE_ALLOWED_USER_IDS.split(",")
            if x.strip()
        ]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "prod"

    @property
    def is_test_mode(self) -> bool:
        return self.APP_MODE == "test"

    def validate_runtime(self):
        if self.PORT <= 0 or self.PORT > 65535:
            raise ValueError("PORT must be between 1 and 65535")

        if self.DB_PORT <= 0 or self.DB_PORT > 65535:
            raise ValueError("DB_PORT must be between 1 and 65535")

        if not self.DB_HOST.strip():
            raise ValueError("DB_HOST is required")

        if not self.DB_NAME.strip():
            raise ValueError("DB_NAME is required")

        if not self.DB_USER.strip():
            raise ValueError("DB_USER is required")

        if self.RISK_CAPITAL_USDT <= 0:
            raise ValueError("RISK_CAPITAL_USDT must be greater than 0")

        if self.RISK_PER_TRADE_PERCENT <= 0 or self.RISK_PER_TRADE_PERCENT > 100:
            raise ValueError("RISK_PER_TRADE_PERCENT must be between 0 and 100")

        if self.MAX_OPEN_TRADES <= 0:
            raise ValueError("MAX_OPEN_TRADES must be greater than 0")

        if self.DAILY_LOSS_LIMIT_USDT <= 0:
            raise ValueError("DAILY_LOSS_LIMIT_USDT must be greater than 0")

        if self.MAX_NOTIONAL_PER_TRADE <= 0:
            raise ValueError("MAX_NOTIONAL_PER_TRADE must be greater than 0")

        if self.SCAN_INTERVAL_SECONDS <= 0:
            raise ValueError("SCAN_INTERVAL_SECONDS must be greater than 0")

        if self.PERFORMANCE_CHECK_INTERVAL_SECONDS <= 0:
            raise ValueError("PERFORMANCE_CHECK_INTERVAL_SECONDS must be greater than 0")

        if self.PAPER_TRADE_CHECK_INTERVAL_SECONDS <= 0:
            raise ValueError("PAPER_TRADE_CHECK_INTERVAL_SECONDS must be greater than 0")

        if self.ALERT_COOLDOWN_SECONDS <= 0:
            raise ValueError("ALERT_COOLDOWN_SECONDS must be greater than 0")

        if self.SCANNER_MAX_SYMBOLS_PER_SCAN <= 0:
            raise ValueError("SCANNER_MAX_SYMBOLS_PER_SCAN must be greater than 0")

        if self.SCANNER_RESULTS_LIMIT <= 0:
            raise ValueError("SCANNER_RESULTS_LIMIT must be greater than 0")

        if self.SCANNER_MIN_QUOTE_VOLUME_5M < 0:
            raise ValueError("SCANNER_MIN_QUOTE_VOLUME_5M must be >= 0")

        if self.SCANNER_MIN_PRICE_CHANGE_5M < 0:
            raise ValueError("SCANNER_MIN_PRICE_CHANGE_5M must be >= 0")

        if self.SCANNER_MIN_VOLUME_SPIKE_RATIO < 0:
            raise ValueError("SCANNER_MIN_VOLUME_SPIKE_RATIO must be >= 0")

        if self.TEST_MODE_COOLDOWN_SECONDS <= 0:
            raise ValueError("TEST_MODE_COOLDOWN_SECONDS must be greater than 0")

        if self.KILL_SWITCH:
            return

        if not self.TELEGRAM_ALLOWED_USER_IDS.strip():
            raise ValueError("TELEGRAM_ALLOWED_USER_IDS is required")

        if self.ENABLE_LIVE_TRADING:
            if self.REQUIRE_PROD_FOR_LIVE and not self.is_production:
                raise ValueError("LIVE trading requires APP_ENV=prod")

            if not self.LIVE_ALLOWED_USER_IDS.strip():
                raise ValueError("LIVE trading requires LIVE_ALLOWED_USER_IDS")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_runtime()
    return settings