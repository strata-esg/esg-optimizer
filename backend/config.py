"""
ESG Optimizer MVP — Configuration centralisée.
Charge les variables d'environnement via pydantic-settings.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Toutes les variables d'environnement du backend, typées et validées."""

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- OpenAI ---
    openai_api_key: str = ""

    # --- JWT ---
    jwt_secret: str = "CHANGE_ME"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # --- Database ---
    database_url: str = "sqlite:///./data/esg_optimizer.db"

    # --- Upload ---
    max_upload_size_mb: int = 20
    max_text_length: int = 30_000

    # --- Freemium ---
    free_tier_monthly_limit: int = 1

    # --- Environment ---
    environment: str = "development"

    @property
    def is_dev(self) -> bool:
        return self.environment == "development"


# Singleton — importé partout via `from config import settings`
settings = Settings()
