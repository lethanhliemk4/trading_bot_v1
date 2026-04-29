from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Binance Insight Dashboard"
    APP_ENV: str = "dev"
    APP_VERSION: str = "1.0.0"

    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8001

    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "binance_bot"
    DB_USER: str = "botuser"
    DB_PASSWORD: str = "change_me"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


settings = Settings()