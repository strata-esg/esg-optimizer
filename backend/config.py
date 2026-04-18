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

    # --- Plans & quotas ---
    # discovery = 1 analyse total (pas par mois), essential = paiement à l'unité,
    # pro = illimité, enterprise = illimité
    discovery_total_limit: int = 1
    essential_analysis_price_eur: int = 39
    pro_monthly_price_eur: int = 129
    pro_annual_price_eur: int = 990

    # --- Analytics (Umami) ---
    umami_url: str = ""
    umami_website_id: str = ""

    # --- Email (Resend) — sprint 6E ---
    resend_api_key: str = ""

    # --- Stripe — sprint 6D ---
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_essential_payment_link: str = ""
    stripe_pro_monthly_payment_link: str = ""
    stripe_pro_annual_payment_link: str = ""

    # --- Environment ---
    environment: str = "development"

    @property
    def is_dev(self) -> bool:
        return self.environment == "development"


# Singleton — importé partout via `from config import settings`
settings = Settings()
