"""
ESG Optimizer MVP - Page Tarifs & Pricing.
Affiche les 4 plans, comparatif des features, FAQ, et CTA Stripe Payment Links.
"""

import streamlit as st
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from frontend.components.analytics import track_event, track_pricing_plan_click, track_payment_completed
from frontend.utils.session import get_token, get_user, is_logged_in, save_user
from frontend.utils.api_client import APIError, get_upgrade_url, get_me
from frontend.utils.styles import inject_global_styles

# Juste après st.set_page_config(...)
from frontend.components.seo import seo_for
seo_for("pricing")
inject_global_styles()

# CSS spécifique : alignement parfait des 4 cards + bouton CTA aligné en bas
st.markdown(
    """
    <style>
    /* Force toutes les cards de plan à avoir la même hauteur */
    .esg-pricing-row [data-testid="column"] > div:first-child {
        height: 100%;
    }
    /* Wrapper card flex-column pour aligner le bouton en bas */
    .esg-plan-wrap {
        display: flex;
        flex-direction: column;
        height: 100%;
        min-height: 460px;
    }
    .esg-plan-wrap .esg-plan-card {
        flex: 1;
        display: flex;
        flex-direction: column;
    }
    /* Espacement homogène autour du bouton CTA */
    .esg-pricing-row .stButton {
        margin-top: 14px;
    }
    /* Masquer le hint "Press Enter to submit form" */
    [data-testid="InputInstructions"] { display: none !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# -- Détection paiement complété (redirect Stripe depuis 6_Tarifs) -------------
_qp = st.query_params
_ps = _qp.get("payment_success", None)
_pp = _qp.get("plan", None)
if _ps == "1" and _pp in ("essential", "pro"):
    track_payment_completed(_pp)  # Event #6 funnel
    st.toast(f"Paiement confirmé - bienvenue sur le plan {_pp.title()} !")
    _tok = get_token()
    if _tok:
        try:
            _fresh = get_me(_tok)
            save_user(_fresh)
        except Exception:
            pass

# -- Auto-refresh du plan utilisateur (capture les essais Pro et code promos
#    dès que le webhook Stripe a tagué le compte côté backend) ---------------
if is_logged_in():
    _tok_auto = get_token()
    if _tok_auto:
        try:
            _fresh_auto = get_me(_tok_auto)
            save_user(_fresh_auto)
        except Exception:
            pass

# -- Tracking vue page ---------------------------------------------------------
track_event("pricing_viewed")

# Header
st.markdown(
    """<div style="text-align: center; padding: 20px 0 36px 0;">
        <div style="font-family:'DM Serif Display',Georgia,serif; font-size:2.4rem;
            font-weight:400; color:#1A3D22; letter-spacing:-0.02em; margin-bottom:10px;
            line-height:1.15;">
            Tarifs simples, sans engagement
        </div>
        <p style="font-family:'DM Sans',sans-serif; font-size:16px; color:#6B7280;
            max-width:560px; margin:0 auto; line-height:1.6;">
            Commencez gratuitement. Passez au supérieur quand vous êtes prêt.
        </p>
    </div>""",
    unsafe_allow_html=True,
)

# Plans data
PLANS = [
    {
        "name": "Découverte",
        "slug": "discovery",
        "price": "0€",
        "period": "1 analyse offerte",
        "description": "Testez l'IA sur votre rapport ESG",
        "recommended": False,
        "features": [
            ("1 analyse complète", True),
            ("Score E/S/G + Global", True),
            ("Conformité CSRD", True),
            ("Synthèse exécutive", True),
            ("Rapport PDF", False),
            ("Delta Report N vs N-1", False),
            ("Export Excel KPIs", False),
            ("Benchmark sectoriel", False),
            ("White-label", False),
            ("Support prioritaire", False),
        ],
        "cta_label": "Commencer gratuitement",
        "cta_action": "register",
    },
    {
        "name": "Essentiel",
        "slug": "essential",
        "price": "39€",
        "period": "par analyse",
        "description": "L'analyse complète à la demande",
        "recommended": False,
        "features": [
            ("Analyses à l'unité", True),
            ("Score E/S/G + Global", True),
            ("Conformité CSRD", True),
            ("Synthèse exécutive", True),
            ("Rapport PDF complet", True),
            ("Delta Report N vs N-1", True),
            ("Conservation 12 mois", True),
            ("Export Excel KPIs", False),
            ("Benchmark sectoriel", False),
            ("White-label", False),
        ],
        "cta_label": "Acheter une analyse",
        "cta_action": "stripe_essential",
    },
    {
        "name": "Pro",
        "slug": "pro",
        "price": "129€",
        "period": "/mois ou 990€/an",
        "description": "Pour les équipes RSE et consultants",
        "recommended": True,
        "features": [
            ("Analyses illimitées", True),
            ("Score E/S/G + Global", True),
            ("Conformité CSRD", True),
            ("Synthèse exécutive", True),
            ("Rapport PDF complet", True),
            ("Delta Report N vs N-1", True),
            ("Historique illimité", True),
            ("Export Excel KPIs", True),
            ("Benchmark sectoriel", True),
            ("Rapport white-label", True),
        ],
        "cta_label": "Démarrer l'essai Pro",
        "cta_action": "stripe_pro",
    },
    {
        "name": "Enterprise",
        "slug": "enterprise",
        "price": "Sur mesure",
        "period": "devis personnalisé",
        "description": "Multi-sites, SSO, API, hébergement dédié",
        "recommended": False,
        "features": [
            ("Tout le plan Pro", True),
            ("SSO / SAML", True),
            ("Multi-utilisateurs", True),
            ("Accès API", True),
            ("Hébergement dédié", True),
            ("SLA garanti", True),
            ("Account manager", True),
            ("Onboarding dédié", True),
            ("Personnalisation", True),
            ("Facturation annuelle", True),
        ],
        "cta_label": "Nous contacter",
        "cta_action": "contact",
    },
]


# Helper : générer une card de plan (HTML card identique à la homepage)
def _render_plan_card(plan: dict, user_plan: str | None) -> None:
    """Affiche une card de plan avec ses features - HTML cards style homepage."""
    is_recommended = plan["recommended"]
    is_current = user_plan == plan["slug"]

    # Couleurs par plan
    _colors = {
        "discovery":  ("#E5E7EB", "1px",  "#1A3D22", "#F9FAFB"),
        "essential":  ("#E5E7EB", "1px",  "#2563EB", "#F9FAFB"),
        "pro":        ("#1A3D22", "2px",  "#1A3D22", "#F0FDF4"),
        "enterprise": ("#E5E7EB", "1px",  "#7C3AED", "#F9FAFB"),
    }
    border_color, border_w, price_color, bg = _colors.get(plan["slug"], _colors["discovery"])

    # Badge "RECOMMANDÉ"
    rec_badge = (
        '<div style="position:absolute;top:-13px;left:50%;transform:translateX(-50%);'
        'background:#1A3D22;color:white;padding:3px 14px;border-radius:10px;'
        'font-size:11px;font-weight:700;letter-spacing:0.5px;white-space:nowrap;">RECOMMANDÉ</div>'
        if is_recommended else ""
    )

    # Badge "Votre plan actuel" - placeholder invisible si non-courant pour garder la même hauteur
    current_badge = (
        '<div style="background:#D4F0D8;color:#1A3D22;text-align:center;padding:6px 10px;'
        'border-radius:6px;font-size:12px;font-weight:600;margin:8px 0;">Votre plan actuel ✓</div>'
        if is_current else
        '<div style="height:36px;margin:8px 0;"></div>'
    )

    # Liste des features
    features_html = ""
    for feat_name, included in plan["features"]:
        if included:
            features_html += (
                f'<div style="display:flex;align-items:flex-start;gap:6px;margin-bottom:4px;">'
                f'<span style="color:#1A3D22;flex-shrink:0;">&#10003;</span>'
                f'<span>{feat_name}</span></div>'
            )
        else:
            features_html += (
                f'<div style="display:flex;align-items:flex-start;gap:6px;margin-bottom:4px;">'
                f'<span style="color:#B53030;flex-shrink:0;">&#10007;</span>'
                f'<span style="color:#9CA3AF;text-decoration:line-through;">{feat_name}</span></div>'
            )

    # Wrapper "esg-plan-wrap" + carte interne avec hauteur 100% pour alignement parfait
    # Toutes les cards (y compris la recommandée) ont la MEME taille/padding/min-height.
    html = (
        f'<div class="esg-plan-wrap">'
        f'<div class="esg-plan-card" style="background:{bg};border:{border_w} solid {border_color};'
        f'border-radius:14px;padding:32px 18px 22px 18px;text-align:center;'
        f'height:490px;overflow:visible;'
        f'position:relative;box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
        f'{rec_badge}'
        f'<div style="font-weight:700;font-size:16px;color:#111827;">{plan["name"]}</div>'
        f'<div style="font-size:32px;font-weight:800;color:{price_color};margin:12px 0 4px 0;line-height:1;">{plan["price"]}</div>'
        f'<div style="font-size:12px;color:#9CA3AF;margin-bottom:6px;min-height:18px;">{plan["period"]}</div>'
        f'<div style="font-size:12px;color:#6B7280;margin-bottom:10px;min-height:32px;">{plan["description"]}</div>'
        f'{current_badge}'
        f'<div style="border-top:1px solid #E5E7EB;margin:10px 0 14px;"></div>'
        f'<div style="text-align:left;font-size:12.5px;color:#374151;line-height:1.85;flex:1;">{features_html}</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# Affichage des 4 plans
user_plan = None
token = None
if is_logged_in():
    user = get_user()
    if user:
        user_plan = user.get("plan", "discovery")
    token = get_token()

# Pré-fetch des URLs Stripe au chargement (évite le pattern rerun)
stripe_urls: dict[str, str] = {}
if is_logged_in() and token:
    for _sp in ("essential", "pro"):
        try:
            _r = get_upgrade_url(token, _sp)
            stripe_urls[_sp] = _r.get("url", "")
        except Exception:
            stripe_urls[_sp] = ""

# Bouton "Actualiser mon plan" - visible après paiement
if is_logged_in():
    col_refresh, _ = st.columns([2, 3])
    with col_refresh:
        if st.button("J'ai payé / activé mon essai - actualiser mon plan",
                     key="refresh_plan_global", use_container_width=True):
            _tok_r = get_token()
            if _tok_r:
                try:
                    _fresh_r = get_me(_tok_r)
                    save_user(_fresh_r)
                    st.success("Plan mis à jour !")
                    st.rerun()
                except Exception:
                    st.error("Impossible de rafraîchir. Réessayez dans quelques instants.")

# Wrapper class pour cibler les cards via CSS
st.markdown('<div class="esg-pricing-row">', unsafe_allow_html=True)
cols = st.columns(4, gap="small")

for i, plan in enumerate(PLANS):
    with cols[i]:
        _render_plan_card(plan, user_plan)

        action = plan["cta_action"]
        is_current = user_plan == plan["slug"]

        if is_current:
            st.button(
                "Plan actuel",
                key=f"btn_{plan['slug']}",
                use_container_width=True,
                disabled=True,
            )
        elif action == "register":
            if is_logged_in():
                st.button(
                    "Inclus",
                    key=f"btn_{plan['slug']}",
                    use_container_width=True,
                    disabled=True,
                )
            else:
                if st.button(
                    plan["cta_label"],
                    key=f"btn_{plan['slug']}",
                    use_container_width=True,
                    type="primary",
                ):
                    track_pricing_plan_click("discovery", source="pricing_page")  # Event #5 funnel
                    st.switch_page("pages/1_Login.py")

        elif action in ("stripe_essential", "stripe_pro"):
            stripe_plan = "essential" if action == "stripe_essential" else "pro"
            btn_type = "primary" if plan["recommended"] else "secondary"

            if not is_logged_in():
                if st.button(plan["cta_label"], key=f"btn_{plan['slug']}",
                             use_container_width=True, type=btn_type):
                    track_pricing_plan_click(stripe_plan, source="pricing_page")  # Event #5 funnel
                    st.switch_page("pages/1_Login.py")
            else:
                url = stripe_urls.get(stripe_plan, "")
                if url:
                    st.link_button(plan["cta_label"], url,
                                   use_container_width=True, type=btn_type)
                else:
                    if st.button(plan["cta_label"], key=f"btn_{plan['slug']}",
                                 use_container_width=True, type=btn_type):
                        track_pricing_plan_click(stripe_plan, source="pricing_page")  # Event #5 funnel
                        st.error("Lien Stripe indisponible. Réessayez.")

        elif action == "contact":
            st.link_button(
                plan["cta_label"],
                "mailto:contact@esg-optimizer.fr?subject=Demande%20Enterprise%20ESG%20Optimizer",
                use_container_width=True,
            )

# Comparatif détaillé
st.markdown("---")
st.markdown(
    """<div style="text-align: center; padding: 20px 0;">
        <h2 style="font-size: 28px; font-weight: 700; color: #111827;">Comparatif détaillé</h2>
    </div>""",
    unsafe_allow_html=True,
)

# Table de comparaison
comparison_features = [
    ("Nombre d'analyses", "1 offerte", "À l'unité (39€)", "Illimitées", "Illimitées"),
    ("Scores E / S / G / Global", "✓", "✓", "✓", "✓"),
    ("Conformité CSRD / ESRS", "✓", "✓", "✓", "✓"),
    ("Synthèse exécutive IA", "✓", "✓", "✓", "✓"),
    ("KPIs détectés", "✓", "✓", "✓", "✓"),
    ("Points forts & lacunes", "✓", "✓", "✓", "✓"),
    ("Recommandations priorisées", "✓", "✓", "✓", "✓"),
    ("Rapport PDF complet", "-", "✓", "✓", "✓"),
    ("Delta Report (N vs N-1)", "-", "✓", "✓", "✓"),
    ("Conservation des données", "30 jours", "12 mois", "Illimitée", "Illimitée"),
    ("Export Excel des KPIs", "-", "-", "✓", "✓"),
    ("Benchmark sectoriel", "-", "-", "✓", "✓"),
    ("Rapport white-label", "-", "-", "✓", "✓"),
    ("Partage LinkedIn (badge)", "-", "✓", "✓", "✓"),
    ("SSO / SAML", "-", "-", "-", "✓"),
    ("Multi-utilisateurs", "-", "-", "-", "✓"),
    ("Accès API", "-", "-", "-", "✓"),
    ("Hébergement dédié", "-", "-", "-", "✓"),
    ("Support", "Email", "Email", "Prioritaire", "Account manager"),
]

# Construire le HTML du tableau
header_row = (
    '<tr style="background: #F9FAFB;">'
    '<th style="padding: 12px 16px; text-align: left; font-weight: 600; color: #374151; border-bottom: 2px solid #E5E7EB;">Feature</th>'
    '<th style="padding: 12px 16px; text-align: center; font-weight: 600; color: #374151; border-bottom: 2px solid #E5E7EB;">Découverte</th>'
    '<th style="padding: 12px 16px; text-align: center; font-weight: 600; color: #374151; border-bottom: 2px solid #E5E7EB;">Essentiel</th>'
    '<th style="padding: 12px 16px; text-align: center; font-weight: 700; color: #1A3D22; border-bottom: 2px solid #1A3D22;">Pro</th>'
    '<th style="padding: 12px 16px; text-align: center; font-weight: 600; color: #374151; border-bottom: 2px solid #E5E7EB;">Enterprise</th>'
    '</tr>'
)

body_rows = ""
for idx, (feat, d, e, p, ent) in enumerate(comparison_features):
    bg = "#FFFFFF" if idx % 2 == 0 else "#F9FAFB"

    def _cell(val: str) -> str:
        if val == "✓":
            return '<span style="color: #1A3D22; font-weight: 700; font-size: 16px;">✓</span>'
        elif val == "-":
            return '<span style="color: #D1D5DB;">-</span>'
        return f'<span style="color: #374151; font-size: 13px;">{val}</span>'

    body_rows += (
        f'<tr style="background: {bg};">'
        f'<td style="padding: 10px 16px; border-bottom: 1px solid #F3F4F6; font-size: 13px; color: #374151;">{feat}</td>'
        f'<td style="padding: 10px 16px; border-bottom: 1px solid #F3F4F6; text-align: center;">{_cell(d)}</td>'
        f'<td style="padding: 10px 16px; border-bottom: 1px solid #F3F4F6; text-align: center;">{_cell(e)}</td>'
        f'<td style="padding: 10px 16px; border-bottom: 1px solid #F3F4F6; text-align: center; background: #F0FDF410;">{_cell(p)}</td>'
        f'<td style="padding: 10px 16px; border-bottom: 1px solid #F3F4F6; text-align: center;">{_cell(ent)}</td>'
        f'</tr>'
    )

st.markdown(
    f"""<div style="overflow-x: auto;">
        <table style="width: 100%; border-collapse: collapse; border-radius: 12px; overflow: hidden; border: 1px solid #E5E7EB;">
            <thead>{header_row}</thead>
            <tbody>{body_rows}</tbody>
        </table>
    </div>""",
    unsafe_allow_html=True,
)

# FAQ Pricing
st.markdown("---")
st.markdown(
    """<div style="text-align: center; padding: 20px 0;">
        <h2 style="font-size: 28px; font-weight: 700; color: #111827;">Questions fréquentes</h2>
    </div>""",
    unsafe_allow_html=True,
)

faq_items = [
    (
        "Puis-je tester avant d'acheter ?",
        "Oui ! Le plan Découverte vous offre une analyse complète gratuite. "
        "Vous obtenez vos scores E/S/G, la conformité CSRD, et des recommandations priorisées. "
        "C'est la même IA que les plans payants - seule la durée de conservation et le PDF complet changent.",
    ),
    (
        "Comment fonctionne le plan Essentiel à 39€ ?",
        "C'est un paiement à l'unité. Chaque fois que vous avez besoin d'analyser un rapport ESG, "
        "vous payez 39€ et obtenez l'analyse complète avec rapport PDF, Delta Report, et conservation 12 mois. "
        "Parfait pour les PME qui ont 1 à 3 rapports par an.",
    ),
    (
        "Le plan Pro est-il un abonnement ?",
        "Oui, le plan Pro est un abonnement mensuel à 129€/mois (ou 990€/an, soit 2 mois offerts). "
        "Vous avez des analyses illimitées, l'export Excel, le benchmark sectoriel, et le white-label. "
        "Vous pouvez résilier à tout moment.",
    ),
    (
        "Que contient le plan Enterprise ?",
        "Le plan Enterprise inclut tout le plan Pro, plus : SSO/SAML, multi-utilisateurs, "
        "accès API, hébergement dédié, SLA garanti, et un account manager dédié. "
        "Contactez-nous à contact@esg-optimizer.fr pour un devis personnalisé.",
    ),
    (
        "Quels formats de rapport sont acceptés ?",
        "ESG Optimizer accepte les fichiers PDF, Word (.docx), et Excel (.xlsx). "
        "L'IA extrait automatiquement le texte et les données de vos rapports de durabilité, "
        "DPEF, rapports RSE, ou tout document ESG.",
    ),
    (
        "Comment l'IA analyse-t-elle mon rapport ?",
        "ESG Optimizer utilise GPT-4o (OpenAI) pour analyser votre rapport contre les 10 normes ESRS "
        "de la directive CSRD. L'IA détecte les KPIs, évalue la couverture de chaque norme, "
        "et génère des recommandations priorisées avec un score de 0 à 100.",
    ),
    (
        "Mes données sont-elles sécurisées ?",
        "Oui. Vos rapports sont traités par l'API OpenAI (pas de rétention côté OpenAI), "
        "et stockés de manière chiffrée. Nous ne partageons jamais vos données avec des tiers. "
        "Le plan Enterprise offre un hébergement dédié pour une isolation complète.",
    ),
    (
        "Puis-je changer de plan à tout moment ?",
        "Oui, vous pouvez passer du plan Découverte à Essentiel ou Pro à tout moment. "
        "Le changement est immédiat. Pour passer en Enterprise, contactez notre équipe commerciale.",
    ),
]

for question, answer in faq_items:
    with st.expander(question):
        st.markdown(answer)

# CTA final
st.markdown("---")
st.markdown(
    """<div style="text-align: center; padding: 30px 0;">
        <div style="font-size: 24px; font-weight: 700; color: #111827; margin-bottom: 8px;">
            Prêt à optimiser votre conformité ESG ?
        </div>
        <div style="font-size: 16px; color: #6B7280; margin-bottom: 20px;">
            Commencez gratuitement - aucune carte bancaire requise.
        </div>
    </div>""",
    unsafe_allow_html=True,
)

col_cta1, col_cta2, col_cta3 = st.columns([1, 2, 1])
with col_cta2:
    if not is_logged_in():
        if st.button(
            "Créer mon compte gratuit",
            use_container_width=True,
            type="primary",
            key="cta_final_register",
        ):
            st.switch_page("pages/1_Login.py")
    else:
        if user_plan in ("discovery", "free", None):
            url_pro = stripe_urls.get("pro", "")
            if url_pro:
                st.link_button("Passer au plan Pro", url_pro,
                               use_container_width=True, type="primary")
            else:
                if st.button("Passer au plan Pro", use_container_width=True,
                             type="primary", key="cta_final_upgrade"):
                    st.error("Lien Stripe indisponible. Réessayez.")
        else:
            _plan_label = {
                "essential": "Essentiel",
                "pro": "Pro",
                "enterprise": "Enterprise",
            }.get(user_plan, str(user_plan).title() if user_plan else "Découverte")
            st.success(f"Vous êtes déjà sur le plan {_plan_label}. Merci pour votre confiance !")
