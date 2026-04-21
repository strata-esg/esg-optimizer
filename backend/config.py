"""
ESG Optimizer MVP — Configuration centralisée.
Charge les variables d'environnement via pydantic-settings.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


# Identité brand
APP_NAME         = "ESG Optimizer"
APP_TAGLINE      = "Êtes-vous prêt pour la CSRD ?"
APP_DESCRIPTION  = "Analysez votre conformité CSRD en 3 minutes avec l'IA"
APP_URL          = os.getenv("APP_URL", "https://esg-optimizer.fr")
APP_VERSION      = "1.0.0"
SUPPORT_EMAIL    = os.getenv("SUPPORT_EMAIL", "hello@esg-optimizer.fr")
NOREPLY_EMAIL    = os.getenv("NOREPLY_EMAIL", "no-reply@esg-optimizer.fr")

# Tokens couleurs (référence unique pour tout le codebase)
BRAND = {
    "forest":      "#1A3D22",
    "forest_mid":  "#2A5C34",
    "leaf":        "#7FC686",
    "mint":        "#D4F0D8",
    "parchment":   "#F5F2EC",
    "amber":       "#C17B2A",
    "alert":       "#B53030",
}

# Plans & pricing (source de vérité pour le frontend et le backend)
PLANS = {
    "discovery": {
        "name": "Découverte", "price": 0, "price_label": "Gratuit",
        "analyses": 1, "watermark": True, "pdf_pages": 3, "delta": False,
        "badge_bg": "#E5E7EB", "badge_color": "#374151",
        "features": ["1 analyse", "Score global", "Rapport partiel (3 pages)"],
    },
    "essential": {
        "name": "Essentiel", "price": 39, "price_label": "39 € / analyse",
        "analyses": 1, "watermark": False, "pdf_pages": 8, "delta": True,
        "badge_bg": "#DBEAFE", "badge_color": "#2563EB",
        "features": ["Rapport complet", "Delta Report", "Conservation 12 mois"],
    },
    "pro": {
        "name": "Pro", "price": 129, "price_label": "129 € / mois",
        "price_annual": 990, "analyses": -1, "watermark": False,
        "pdf_pages": 8, "delta": True,
        "badge_bg": BRAND["mint"], "badge_color": BRAND["forest"],
        "features": ["Illimité", "Benchmark sectoriel", "Export Excel", "White-label"],
    },
    "enterprise": {
        "name": "Enterprise", "price": -1, "price_label": "Sur devis",
        "analyses": -1, "watermark": False, "pdf_pages": 8, "delta": True,
        "badge_bg": "#EDE9FE", "badge_color": "#7C3AED",
        "features": ["SSO", "Multi-users", "API REST", "SLA garanti"],
    },
}


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

    # --- Cron API key (séparer du JWT_SECRET pour la sécurité) ---
    # Générer via : python -c "import secrets;print(secrets.token_urlsafe(32))"
    cron_api_key: str = ""  # Si vide, le digest hebdomadaire est désactivé

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
