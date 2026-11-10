
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# Racine du projet FIDOMEK-ONE
BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Configuration centralisée du backend."""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_NAME: str = "FIDOMEK ONE"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    TIMEZONE: str = "Africa/Casablanca"

    # API
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000

    # Base de données
    DATABASE_URL: str = (
        f"sqlite:///{(BASE_DIR / 'data' / 'fidomek_dev.db').as_posix()}"
    )

    # Stockage documentaire
    STORAGE_DIR: Path = BASE_DIR / "data" / "documents"
    MAX_FILE_SIZE: int = 25 * 1024 * 1024

    ALLOWED_EXTENSIONS: tuple[str, ...] = (
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".csv",
    )

    # Gmail
    GMAIL_CLIENT_SECRET_FILE: Path = BASE_DIR / "client_secret.json"
    GMAIL_TOKEN_FILE: Path = BASE_DIR / "token_cabinet.json"
    GMAIL_CHECK_INTERVAL: int = 300


@lru_cache
def get_settings() -> Settings:
    """Retourne une instance unique de la configuration."""
    return Settings()


settings = get_settings()
