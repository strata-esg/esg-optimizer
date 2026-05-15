"""
Vérification des jetons de session Clerk.

Le frontend Next.js délègue l'authentification à Clerk. Chaque requête vers
l'API porte un jeton de session Clerk signé en RS256. Ce module récupère les
clés publiques (JWKS) de l'instance Clerk, les met en cache, et valide la
signature, l'émetteur et l'expiration du jeton.
"""

import logging
import time

import requests
from jose import jwt
from jose.exceptions import JWTError

from backend.config import settings

logger = logging.getLogger(__name__)

# Cache mémoire des clés JWKS (rafraîchi toutes les heures).
_JWKS_TTL_SECONDS = 3600
_jwks_cache: dict = {"keys": None, "fetched_at": 0.0}


def _fetch_jwks(force: bool = False) -> list[dict]:
    """Récupère les clés publiques JWKS de Clerk, avec mise en cache."""
    now = time.time()
    cached = _jwks_cache["keys"]
    if not force and cached is not None and (now - _jwks_cache["fetched_at"] < _JWKS_TTL_SECONDS):
        return cached

    jwks_url = settings.resolved_clerk_jwks_url
    if not jwks_url:
        return []

    response = requests.get(jwks_url, timeout=5)
    response.raise_for_status()
    keys = response.json().get("keys", [])
    _jwks_cache["keys"] = keys
    _jwks_cache["fetched_at"] = now
    return keys


def _find_key(kid: str) -> dict | None:
    """Cherche la clé correspondant au kid, avec un rafraîchissement si besoin."""
    keys = _fetch_jwks()
    key = next((k for k in keys if k.get("kid") == kid), None)
    if key is None:
        # La clé a peut-être été tournée côté Clerk : on force un rafraîchissement.
        keys = _fetch_jwks(force=True)
        key = next((k for k in keys if k.get("kid") == kid), None)
    return key


def verify_clerk_token(token: str) -> dict | None:
    """
    Valide un jeton de session Clerk.

    Retourne le payload décodé si le jeton est valide, sinon None
    (jeton absent, mal formé, expiré, ou émis par une autre instance).
    """
    issuer = settings.clerk_issuer.rstrip("/")
    if not issuer or not token:
        return None

    try:
        header = jwt.get_unverified_header(token)
    except JWTError:
        return None

    kid = header.get("kid")
    if not kid or header.get("alg") != "RS256":
        return None

    try:
        key = _find_key(kid)
    except requests.RequestException as exc:
        logger.warning("Impossible de récupérer les clés JWKS Clerk : %s", exc)
        return None

    if key is None:
        return None

    try:
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            issuer=issuer,
            # Les jetons de session Clerk portent 'azp' (origine autorisée),
            # pas 'aud'. On désactive donc la vérification d'audience.
            # Les jetons Clerk sont à durée de vie courte : on tolère un léger
            # décalage d'horloge entre le serveur et Clerk.
            options={"verify_aud": False, "leeway": 30},
        )
        return payload
    except JWTError as exc:
        logger.debug("Jeton Clerk rejeté : %s", exc)
        return None
