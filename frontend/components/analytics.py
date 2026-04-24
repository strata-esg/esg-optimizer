"""
ESG Optimizer MVP — Composant analytics Umami.
Injecte le script de tracking Umami et expose les helpers du funnel de conversion.

Configuration :
    - Variable d'environnement UMAMI_WEBSITE_ID (UUID du site dans le dashboard Umami)
    - Ex : UMAMI_WEBSITE_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

Funnel de conversion (6 events) :
    1. cta_landing_click     — Clic sur un CTA de la landing page
    2. quick_check_submit    — Soumission du formulaire quick-check (fichier déposé)
    3. upload_started        — Début d'upload d'analyse (utilisateur authentifié)
    4. analysis_completed    — Fin d'analyse avec succès
    5. pricing_plan_click    — Clic sur un plan tarifaire
    6. payment_completed     — Paiement Stripe complété (via ?payment_success=1)
"""

import streamlit as st
import os

# ── Config ────────────────────────────────────────────────────────────────────
UMAMI_WEBSITE_ID = os.getenv("UMAMI_WEBSITE_ID", "")


# ── Injection du script ───────────────────────────────────────────────────────

def inject_analytics_script() -> None:
    """
    Injecte le script Umami dans la page Streamlit.
    Ne fait rien si UMAMI_WEBSITE_ID n'est pas configuré (mode dev).
    Appeler UNE SEULE FOIS par page, typiquement dans app.py.
    """
    if not UMAMI_WEBSITE_ID:
        return

    script = f"""
    <script async src="https://cloud.umami.is/script.js"
            data-website-id="{UMAMI_WEBSITE_ID}">
    </script>
    <script>
        // Stub de secours — garantit que umami.track() ne lève pas d'erreur
        // si le script CDN n'est pas encore chargé au moment du premier event
        if (typeof window.umami === 'undefined') {{
            window.umami = {{
                track: function(name, data) {{
                    window._umamiQueue = window._umamiQueue || [];
                    window._umamiQueue.push({{ name: name, data: data }});
                }}
            }};
        }}
    </script>
    """
    st.markdown(script, unsafe_allow_html=True)


# Alias rétro-compat
inject_umami_script = inject_analytics_script


# ── Moteur de tracking ────────────────────────────────────────────────────────

def track_event(event_name: str, data: dict | None = None) -> None:
    """
    Envoie un event custom à Umami via JavaScript.

    Args:
        event_name : Nom de l'event tel que configuré dans Umami
                     (ex: 'cta_landing_click')
        data       : Propriétés additionnelles (ex: {'plan': 'pro', 'score': 72})
    """
    if not UMAMI_WEBSITE_ID:
        return  # Mode dev — skip silencieusement

    import json
    data_js = json.dumps(data) if data else "undefined"

    js = f"""
    <script>
        (function() {{
            function _fire() {{
                if (typeof umami !== 'undefined' && typeof umami.track === 'function') {{
                    umami.track('{event_name}', {data_js});
                }}
            }}
            // Si le DOM est prêt, fire tout de suite ; sinon, attendre load
            if (document.readyState === 'complete') {{
                _fire();
            }} else {{
                window.addEventListener('load', _fire, {{ once: true }});
            }}
        }})();
    </script>
    """
    st.markdown(js, unsafe_allow_html=True)


# ── 6 events du funnel de conversion ─────────────────────────────────────────

def track_cta_landing_click(cta_label: str = "unknown", source: str = "landing") -> None:
    """
    1. Clic sur un CTA de la landing page.

    Args:
        cta_label : Texte du bouton cliqué (ex: 'Analyser gratuitement')
        source    : Section d'origine (ex: 'hero', 'pricing', 'footer_cta')
    """
    track_event("cta_landing_click", {"cta_label": cta_label, "source": source})


def track_quick_check_submit(filename: str | None = None) -> None:
    """
    2. Soumission du formulaire quick-check (fichier déposé sans compte).

    Args:
        filename : Nom du fichier uploadé (ex: 'rapport_rse_2025.pdf')
    """
    data: dict = {}
    if filename:
        # Stocker uniquement l'extension, pas le nom complet (RGPD)
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "unknown"
        data["format"] = ext
    track_event("quick_check_submit", data or None)


def track_upload_started(company_name: str | None = None, sector: str | None = None) -> None:
    """
    3. Début d'upload d'analyse (utilisateur authentifié, rapport soumis).

    Args:
        company_name : Nom de l'entreprise analysée (facultatif)
        sector       : Secteur sélectionné dans le formulaire (facultatif)
    """
    data: dict = {}
    if sector:
        data["sector"] = sector
    # company_name volontairement exclu des propriétés (peut contenir des données sensibles)
    track_event("upload_started", data or None)


def track_analysis_completed(score: float | None = None, plan: str | None = None) -> None:
    """
    4. Fin d'analyse avec succès — event le plus précieux du funnel.

    Args:
        score : Score global ESG (0-100)
        plan  : Plan de l'utilisateur au moment de l'analyse
    """
    data: dict = {}
    if score is not None:
        # Arrondir pour éviter des valeurs parasites dans Umami
        data["score_global"] = round(float(score), 1)
        # Catégorie de score pour segmentation rapide
        if score >= 70:
            data["score_tier"] = "high"
        elif score >= 40:
            data["score_tier"] = "medium"
        else:
            data["score_tier"] = "low"
    if plan:
        data["plan"] = plan
    track_event("analysis_completed", data or None)


def track_pricing_plan_click(plan: str, source: str = "pricing_page") -> None:
    """
    5. Clic sur un plan tarifaire (bouton CTA de la card de plan).

    Args:
        plan   : Slug du plan cliqué ('discovery', 'essential', 'pro', 'enterprise')
        source : Page d'origine ('pricing_page', 'homepage', 'upgrade_prompt')
    """
    track_event("pricing_plan_click", {"plan": plan, "source": source})


def track_payment_completed(plan: str) -> None:
    """
    6. Paiement Stripe complété — détecté via ?payment_success=1&plan=... dans l'URL.

    Note : Configurer le success URL du Payment Link Stripe vers :
        https://<app-url>/?payment_success=1&plan=essential  (plan Essentiel)
        https://<app-url>/?payment_success=1&plan=pro        (plan Pro)

    Args:
        plan : Plan souscrit ('essential' ou 'pro')
    """
    track_event("payment_completed", {"plan": plan})


# ── Helpers legacy (rétro-compat avec l'ancien code Plausible) ────────────────

def track_landing_view(persona: str | None = None) -> None:
    """Legacy — vue de la landing page."""
    track_event("landing_view", {"persona": persona} if persona else None)


def track_quick_check_started() -> None:
    """Legacy → mappé sur track_quick_check_submit."""
    track_event("quick_check_submit")


def track_quick_check_completed(score: float | None = None) -> None:
    """Legacy — quick-check terminé avec score."""
    track_event("quick_check_completed", {"score": score} if score is not None else None)


def track_signup_started(source: str = "direct") -> None:
    """Legacy — formulaire d'inscription ouvert."""
    track_event("signup_started", {"source": source})


def track_signup_completed(source: str = "direct") -> None:
    """Legacy — inscription réussie."""
    track_event("signup_completed", {"source": source})


def track_first_analysis_completed(score: float | None = None) -> None:
    """Legacy → mappé sur track_analysis_completed."""
    track_analysis_completed(score)


def track_pricing_viewed(persona: str | None = None) -> None:
    """Legacy — page tarifs consultée."""
    track_event("pricing_viewed", {"persona": persona} if persona else None)


def track_upgrade_clicked(plan: str = "pro") -> None:
    """Legacy → mappé sur track_pricing_plan_click."""
    track_pricing_plan_click(plan, source="legacy")
