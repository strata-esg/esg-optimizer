"""
ESG Optimizer MVP — Page Tarifs & Pricing.
Affiche les 4 plans, comparatif des features, FAQ, et CTA Stripe Payment Links.
"""

import streamlit as st
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from frontend.components.analytics import track_event
from frontend.utils.session import get_token, get_user, is_logged_in
from frontend.utils.api_client import APIError, get_upgrade_url

# Header
st.markdown(
    """<div style="text-align: center; padding: 20px 0 30px 0;">
        <h1 style="font-size: 36px; font-weight: 800; color: #111827; margin-bottom: 8px;">
            Choisissez votre plan
        </h1>
        <p style="font-size: 18px; color: #6B7280; max-width: 600px; margin: 0 auto;">
            De l'analyse ponctuelle au reporting continu — un plan adapté à chaque besoin ESG.
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
        "cta_label": "Commencer le Pro",
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


# Helper : générer une card de plan (composants natifs)
def _render_plan_card(plan: dict, user_plan: str | None) -> None:
    """Affiche une card de plan avec ses features et CTA — composants Streamlit natifs."""
    is_recommended = plan["recommended"]
    is_current = user_plan == plan["slug"]

    # Badge recommandé
    if is_recommended:
        st.markdown(
            '<p style="background:#1A3D22;color:white;font-size:11px;font-weight:700;'
            'padding:3px 12px;border-radius:8px;text-align:center;letter-spacing:0.5px;'
            'margin-bottom:4px;">RECOMMANDÉ</p>',
            unsafe_allow_html=True,
        )

    # Nom du plan
    st.markdown(f"### {plan['name']}")

    # Prix
    st.markdown(f"**{plan['price']}** {plan['period']}")

    # Description
    st.caption(plan["description"])

    # Badge plan actuel
    if is_current:
        st.info("Votre plan actuel")

    st.markdown("---")

    # Features (une par ligne, simple markdown)
    for feat_name, included in plan["features"]:
        if included:
            st.markdown(f'<span style="color:#1A3D22;">&#10003;</span> {feat_name}', unsafe_allow_html=True)
        else:
            st.markdown(f'<span style="color:#9CA3AF;">&#10007;</span> ~~{feat_name}~~', unsafe_allow_html=True)


# Affichage des 4 plans
user_plan = None
token = None
if is_logged_in():
    user = get_user()
    if user:
        user_plan = user.get("plan", "discovery")
    token = get_token()

cols = st.columns(4, gap="medium")

for i, plan in enumerate(PLANS):
    with cols[i]:
        _render_plan_card(plan, user_plan)
        st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)

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
                    st.switch_page("pages/1_Login.py")

        elif action in ("stripe_essential", "stripe_pro"):
            stripe_plan = "essential" if action == "stripe_essential" else "pro"
            btn_type = "primary" if plan["recommended"] else "secondary"

            if st.button(
                plan["cta_label"],
                key=f"btn_{plan['slug']}",
                use_container_width=True,
                type=btn_type,
            ):
                if not is_logged_in():
                    st.warning("Connectez-vous d'abord pour souscrire.")
                    st.switch_page("pages/1_Login.py")
                else:
                    try:
                        result = get_upgrade_url(token, stripe_plan)
                        url = result.get("url", "")
                        if url:
                            track_event("click_upgrade", {"plan": stripe_plan})
                            st.markdown(
                                f'<meta http-equiv="refresh" content="0;url={url}">',
                                unsafe_allow_html=True,
                            )
                            st.info(f"Redirection vers Stripe... [Cliquez ici si rien ne se passe]({url})")
                    except APIError as e:
                        st.error(f"Erreur : {e.detail}")

        elif action == "contact":
            if st.button(
                plan["cta_label"],
                key=f"btn_{plan['slug']}",
                use_container_width=True,
            ):
                track_event("click_enterprise_contact", {})
                st.markdown(
                    """<div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 12px;
                        padding: 16px; margin-top: 8px; text-align: center;">
                        <div style="font-weight: 600; color: #1E40AF;">Contactez-nous</div>
                        <div style="font-size: 13px; color: #6B7280; margin-top: 4px;">
                            <a href="mailto:contact@esg-optimizer.fr">contact@esg-optimizer.fr</a>
                        </div>
                    </div>""",
                    unsafe_allow_html=True,
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
    ("Rapport PDF complet", "—", "✓", "✓", "✓"),
    ("Delta Report (N vs N-1)", "—", "✓", "✓", "✓"),
    ("Conservation des données", "30 jours", "12 mois", "Illimitée", "Illimitée"),
    ("Export Excel des KPIs", "—", "—", "✓", "✓"),
    ("Benchmark sectoriel", "—", "—", "✓", "✓"),
    ("Rapport white-label", "—", "—", "✓", "✓"),
    ("Partage LinkedIn (badge)", "—", "✓", "✓", "✓"),
    ("SSO / SAML", "—", "—", "—", "✓"),
    ("Multi-utilisateurs", "—", "—", "—", "✓"),
    ("Accès API", "—", "—", "—", "✓"),
    ("Hébergement dédié", "—", "—", "—", "✓"),
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
        elif val == "—":
            return '<span style="color: #D1D5DB;">—</span>'
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
        "C'est la même IA que les plans payants — seule la durée de conservation et le PDF complet changent.",
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
            Commencez gratuitement — aucune carte bancaire requise.
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
        if user_plan in ("discovery", "free"):
            if st.button(
                "Passer au plan Pro",
                use_container_width=True,
                type="primary",
                key="cta_final_upgrade",
            ):
                try:
                    result = get_upgrade_url(token, "pro")
                    url = result.get("url", "")
                    if url:
                        track_event("click_upgrade", {"plan": "pro", "source": "pricing_cta"})
                        st.markdown(
                            f'<meta http-equiv="refresh" content="0;url={url}">',
                            unsafe_allow_html=True,
                        )
                        st.info(f"Redirection vers Stripe... [Cliquez ici]({url})")
                except APIError as e:
                    st.error(f"Erreur : {e.detail}")
        else:
            st.success(f"Vous êtes déjà sur le plan {user_plan.title()}. Merci pour votre confiance !")
