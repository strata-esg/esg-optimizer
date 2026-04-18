"""
ESG Optimizer MVP — Composant analytics Umami.
Injecte le script de tracking Umami et expose des fonctions de tracking d'events.

Configuration :
    - Variable d'environnement UMAMI_WEBSITE_ID (ou laisser vide en dev)
    - Variable d'environnement UMAMI_URL (URL de ton instance Umami self-hosted)

Events trackés :
    1. landing_view         — Page d'accueil affichée
    2. quick_check_started  — Upload public lancé (sans compte)
    3. quick_check_completed — Quick-check terminé avec score
    4. signup_started       — Formulaire d'inscription ouvert
    5. signup_completed     — Inscription réussie
    6. first_analysis_completed — 1ère analyse complète terminée
    7. pricing_viewed       — Page tarifs consultée
    8. upgrade_clicked      — Clic sur un bouton de passage payant
"""

import streamlit as st
import os

# ── Config ────────────────────────────────────────────────────────
UMAMI_URL = os.getenv("UMAMI_URL", "")  # ex: https://umami.esg-optimizer.app
UMAMI_WEBSITE_ID = os.getenv("UMAMI_WEBSITE_ID", "")  # UUID de ton site dans Umami


def inject_umami_script() -> None:
    """
    Injecte le script Umami dans le <head> de la page Streamlit.
    Ne fait rien si UMAMI_URL ou UMAMI_WEBSITE_ID ne sont pas configurés.
    Appeler UNE SEULE FOIS par page, typiquement dans app.py.
    """
    if not UMAMI_URL or not UMAMI_WEBSITE_ID:
        return  # Pas configuré — mode dev, on skip silencieusement

    script = f"""
    <script defer src="{UMAMI_URL}/script.js"
            data-website-id="{UMAMI_WEBSITE_ID}">
    </script>
    """
    st.markdown(script, unsafe_allow_html=True)


def track_event(event_name: str, data: dict | None = None) -> None:
    """
    Envoie un event custom à Umami via JavaScript.

    Args:
        event_name: Nom de l'event (ex: 'quick_check_started')
        data: Données additionnelles (ex: {'persona': 'pme', 'score': 72})
    """
    if not UMAMI_URL or not UMAMI_WEBSITE_ID:
        return

    data_json = ""
    if data:
        import json
        data_json = f", {json.dumps(data)}"

    js = f"""
    <script>
        if (typeof umami !== 'undefined') {{
            umami.track('{event_name}'{data_json});
        }}
    </script>
    """
    st.markdown(js, unsafe_allow_html=True)


# ── Helpers pour les 8 events principaux ──────────────────────────

def track_landing_view(persona: str | None = None) -> None:
    """Track : page d'accueil affichée."""
    track_event("landing_view", {"persona": persona} if persona else None)


def track_quick_check_started() -> None:
    """Track : upload public lancé (sans compte)."""
    track_event("quick_check_started")


def track_quick_check_completed(score: float | None = None) -> None:
    """Track : quick-check terminé avec score."""
    track_event("quick_check_completed", {"score": score} if score else None)


def track_signup_started(source: str = "direct") -> None:
    """Track : formulaire d'inscription ouvert."""
    track_event("signup_started", {"source": source})


def track_signup_completed(source: str = "direct") -> None:
    """Track : inscription réussie."""
    track_event("signup_completed", {"source": source})


def track_first_analysis_completed(score: float | None = None) -> None:
    """Track : 1ère analyse complète terminée."""
    track_event("first_analysis_completed", {"score": score} if score else None)


def track_pricing_viewed(persona: str | None = None) -> None:
    """Track : page tarifs consultée."""
    track_event("pricing_viewed", {"persona": persona} if persona else None)


def track_upgrade_clicked(plan: str = "pro") -> None:
    """Track : clic sur un bouton de passage payant."""
    track_event("upgrade_clicked", {"plan": plan})
