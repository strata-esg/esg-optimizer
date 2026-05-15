"""
ESG Optimizer - Configuration centralisée.
Charge les variables d'environnement via pydantic-settings.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


# Identité brand
APP_NAME         = "ESG Optimizer"
APP_TAGLINE      = "Êtes-vous prêt pour la CSRD ?"
APP_DESCRIPTION  = "Analysez votre conformité CSRD en quelques minutes."
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

    # --- JWT (auth historique, frontend Streamlit) ---
    jwt_secret: str = "CHANGE_ME"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # --- Clerk (auth du frontend Next.js) ---
    # Le frontend Next.js authentifie via Clerk. Le backend vérifie les jetons
    # de session Clerk (RS256) à l'aide des clés publiques JWKS de l'instance.
    # clerk_issuer = l'URL Frontend API de l'instance Clerk.
    # Exemple instance de test : https://proven-firefly-18.clerk.accounts.dev
    clerk_issuer: str = "https://proven-firefly-18.clerk.accounts.dev"
    clerk_jwks_url: str = ""  # Si vide, dérivé de clerk_issuer + /.well-known/jwks.json

    @property
    def resolved_clerk_jwks_url(self) -> str:
        if self.clerk_jwks_url:
            return self.clerk_jwks_url
        if not self.clerk_issuer:
            return ""
        return self.clerk_issuer.rstrip("/") + "/.well-known/jwks.json"

    # --- CORS ---
    # Origines supplémentaires autorisées (séparées par des virgules).
    # Utile pour ajouter le domaine Vercel de production sans toucher au code.
    extra_cors_origins: str = ""

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

    # --- Quick-check public ---
    public_upload_max_mb: int = 10
    public_rate_limit_daily: int = 3
    public_rate_limit_weekly: int = 10
    public_token_expiry_hours: int = 72

    # --- PostHog (product analytics : funnels, session recording) ---
    # Créer un projet sur https://app.posthog.com puis Settings, Project API key.
    # Host : https://eu.i.posthog.com (EU) ou https://us.i.posthog.com (US)
    posthog_api_key: str = ""    # ex: phc_XXXXXXXXXXXX
    posthog_host: str = "https://eu.i.posthog.com"

    # --- Cloudflare R2 (stockage persistant des rapports uploadés) ---
    # Activer en prod pour éviter de perdre les fichiers lors d'un redeploy Railway.
    # En dev, use_r2_storage=False : repli sur tempfile local.
    use_r2_storage: bool = False
    r2_account_id: str = ""           # ex: abc123def456...
    r2_access_key_id: str = ""        # Clé d'accès R2 (depuis Cloudflare Dashboard)
    r2_secret_access_key: str = ""    # Clé secrète R2
    r2_bucket_name: str = "esg-reports"  # Nom du bucket R2

    # --- Redis / Celery ---
    # Upstash Redis URL format: rediss://default:<password>@<host>:<port>
    # En local sans Redis: laisser vide, le backend bascule sur BackgroundTasks FastAPI
    redis_url: str = ""
    # Activer explicitement Celery (ENABLE_CELERY=true dans l'environnement Railway).
    # redis_url seul ne suffit pas : ce flag doit etre true pour dispatcher via Celery.
    enable_celery: bool = False

    # --- Environment ---
    environment: str = "development"

    @property
    def is_dev(self) -> bool:
        return self.environment == "development"


# Singleton, importé partout via `from config import settings`
settings = Settings()
