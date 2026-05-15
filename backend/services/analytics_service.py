"""
ESG Optimizer -- Service PostHog (analytics produit cote serveur).

Pourquoi server-side ?
- Les events critiques (analyse terminee, quota atteint, paiement) ne doivent pas
  dependre du navigateur : bloqueurs de pub, JS desactive, fermeture d'onglet.
- On connait le user_id cote serveur -> events identifies des la premiere action.

Usage :
    from backend.services.analytics_service import ph
    ph.capture(user_id, "analysis_completed", {"score_global": 72.4})
    ph.identify(user_id, email="user@example.com", plan="pro")

Tous les appels sont proteges par try/except : PostHog ne doit jamais faire
echouer une requete metier.
"""

import logging
from typing import Any

from backend.config import settings

logger = logging.getLogger(__name__)

# Client PostHog initialise une seule fois (singleton)
_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    if not settings.posthog_api_key:
        return None
    try:
        import posthog as ph_sdk
        ph_sdk.api_key = settings.posthog_api_key
        ph_sdk.host = settings.posthog_host
        # Desactiver les logs PostHog (verbeux en dev)
        ph_sdk.disabled = False
        _client = ph_sdk
        logger.info("PostHog initialise - host=%s", settings.posthog_host)
        return _client
    except ImportError:
        logger.warning("Librairie posthog non installee - analytics desactivees")
        return None
    except Exception as exc:
        logger.warning("PostHog init echoue : %s", exc)
        return None


def _distinct_id(user_id: int) -> str:
    """Convention : distinct_id = 'user_{id}' pour les events server-side."""
    return f"user_{user_id}"


class _PostHog:
    """Wrapper mince autour du SDK PostHog. Silencieux si la cle est absente."""

    def capture(self, user_id: int, event: str, properties: dict[str, Any] | None = None) -> None:
        """Envoie un event identifie (user connu)."""
        client = _get_client()
        if not client:
            return
        try:
            client.capture(
                distinct_id=_distinct_id(user_id),
                event=event,
                properties=properties or {},
            )
        except Exception as exc:
            logger.debug("PostHog capture echoue (%s) : %s", event, exc)

    def identify(self, user_id: int, **properties) -> None:
        """Met a jour le profil utilisateur dans PostHog."""
        client = _get_client()
        if not client:
            return
        try:
            client.identify(
                distinct_id=_distinct_id(user_id),
                properties=properties,
            )
        except Exception as exc:
            logger.debug("PostHog identify echoue (user=%d) : %s", user_id, exc)

    def capture_anon(self, distinct_id: str, event: str, properties: dict[str, Any] | None = None) -> None:
        """Event anonyme (ex: quick-check public sans user connecte)."""
        client = _get_client()
        if not client:
            return
        try:
            client.capture(distinct_id=distinct_id, event=event, properties=properties or {})
        except Exception as exc:
            logger.debug("PostHog capture_anon echoue (%s) : %s", event, exc)


# Singleton importe partout : from backend.services.analytics_service import ph
ph = _PostHog()
