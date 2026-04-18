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
    # Rétro-compat : si FREE_TIER_MONTHLY_LIMIT existe dans .env, on l'ignore (extra="ignore")

    # --- Analytics (Plausible) ---
    plausible_domain: str = ""  # ex: esg-optimizer.fr

    # --- Email (Resend) ---
    resend_api_key: str = ""

    # --- Stripe ---
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_link_essentiel: str = ""   # Payment Link Stripe pour le plan Essentiel (39€)
    stripe_link_pro: str = ""         # Payment Link Stripe pour le plan Pro (129€/mois)

    # --- Sentry (monitoring erreurs) ---
    sentry_dsn: str = ""

    # --- Quick-check public (sprint 6B) ---
    public_upload_max_mb: int = 10
    public_rate_limit_daily: int = 3
    public_rate_limit_weekly: int = 10
    public_token_expiry_hours: int = 72

    # --- Environment ---
    environment: str = "development"

    @property
    def is_dev(self) -> bool:
        return self.environment == "development"


# Singleton — importé partout via `from config import settings`
settings = Settings()
