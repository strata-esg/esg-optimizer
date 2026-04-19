"""
ESG Optimizer MVP — Composant analytics Plausible.
Injecte le script de tracking Plausible et expose des fonctions de tracking d'events.

Configuration :
    - Variable d'environnement PLAUSIBLE_DOMAIN (ex: esg-optimizer.fr)

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

# Config
PLAUSIBLE_DOMAIN = os.getenv("PLAUSIBLE_DOMAIN", "")  # ex: esg-optimizer.fr


def inject_analytics_script() -> None:
    """
    Injecte le script Plausible dans la page Streamlit.
    Ne fait rien si PLAUSIBLE_DOMAIN n'est pas configuré.
    Appeler UNE SEULE FOIS par page, typiquement dans app.py.
    """
    if not PLAUSIBLE_DOMAIN:
        return  # Pas configuré — mode dev, on skip silencieusement

    script = f"""
    <script defer data-domain="{PLAUSIBLE_DOMAIN}"
            src="https://plausible.io/js/script.js">
    </script>
    <script>window.plausible = window.plausible || function() {{
        (window.plausible.q = window.plausible.q || []).push(arguments)
    }}</script>
    """
    st.markdown(script, unsafe_allow_html=True)


# Alias pour rétro-compat avec le code existant
inject_umami_script = inject_analytics_script


def track_event(event_name: str, data: dict | None = None) -> None:
    """
    Envoie un event custom à Plausible via JavaScript.

    Args:
        event_name: Nom de l'event (ex: 'quick_check_started')
        data: Données additionnelles (ex: {'persona': 'pme', 'score': 72})
    """
    if not PLAUSIBLE_DOMAIN:
        return

    props_json = ""
    if data:
        import json
        props_json = f", {{props: {json.dumps(data)}}}"

    js = f"""
    <script>
        if (typeof plausible !== 'undefined') {{
            plausible('{event_name}'{props_json});
        }}
    </script>
    """
    st.markdown(js, unsafe_allow_html=True)


# Helpers pour les 8 events principaux

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
