from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt, JWTError
from backend.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiration_hours)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    """Renvoie le payload ou None si token invalide/expiré."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None


# ── Feature gating par plan ───────────────────────────────────────
# Hiérarchie : discovery < essential < pro < enterprise
PLAN_HIERARCHY = {
    "discovery": 0,
    "free": 0,       # rétro-compat ancien plan
    "essential": 1,
    "pro": 2,
    "enterprise": 3,
}

# Chaque feature est accessible à partir d'un plan minimum
FEATURE_MIN_PLAN = {
    "full_pdf_report":      "essential",   # Rapport complet sans watermark
    "detailed_scores":      "essential",   # Sous-scores E/S/G détaillés
    "delta_report":         "essential",   # Delta Report
    "data_retention_12m":   "essential",   # Conservation 12 mois
    "excel_export":         "pro",         # Export Excel des KPIs
    "benchmarking":         "pro",         # Benchmark sectoriel
    "white_label":          "pro",         # Rapport white-label
    "unlimited_analyses":   "pro",         # Analyses illimitées
    "unlimited_history":    "pro",         # Historique illimité
    "sso":                  "enterprise",  # SSO / SAML
    "multi_users":          "enterprise",  # Multi-utilisateurs
    "api_access":           "enterprise",  # Accès API
    "dedicated_hosting":    "enterprise",  # Hébergement dédié
}


def check_plan_access(user_plan: str, feature: str) -> bool:
    """
    Vérifie si le plan de l'utilisateur donne accès à une feature.

    Args:
        user_plan: Plan actuel de l'utilisateur ('discovery', 'essential', 'pro', 'enterprise')
        feature: Nom de la feature à vérifier (clé de FEATURE_MIN_PLAN)

    Returns:
        True si l'utilisateur a accès, False sinon.
    """
    user_level = PLAN_HIERARCHY.get(user_plan, 0)
    min_plan = FEATURE_MIN_PLAN.get(feature, "enterprise")
    required_level = PLAN_HIERARCHY.get(min_plan, 3)
    return user_level >= required_level


def get_plan_display_name(plan: str) -> str:
    """Retourne le nom d'affichage du plan."""
    names = {
        "discovery": "Découverte",
        "free": "Découverte",
        "essential": "Essentiel",
        "pro": "Pro",
        "enterprise": "Enterprise",
    }
    return names.get(plan, "Découverte")