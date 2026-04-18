"""
ESG Optimizer MVP — Landing page publique.
Première page Streamlit (préfixe 0_) — accessible sans connexion.
Contient : Hero, cards persona, preuve sociale, démo, comment ça marche,
pricing 4 plans, FAQ, footer.
"""

import streamlit as st
import sys
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────
_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from frontend.components.sidebar import render_sidebar
from frontend.components.analytics import inject_umami_script, track_landing_view, track_pricing_viewed, track_quick_check_started, track_quick_check_completed
from frontend.utils.session import is_logged_in
from frontend.utils.api_client import quick_check_upload, quick_check_result, APIError

# ── Page config ───────────────────────────────────────────────────
render_sidebar()

# ── Analytics ─────────────────────────────────────────────────────
inject_umami_script()

# ── Query params pour persona ─────────────────────────────────────
params = st.query_params
persona = params.get("persona", None)

track_landing_view(persona)

# ── Contenu personnalisé par persona ──────────────────────────────
PERSONA_CONTENT = {
    "pme": {
        "titre": "PME : Votre rapport CSRD est-il conforme ?",
        "sous_titre": "Pas besoin d'un cabinet à 15 000 €. En 3 minutes, notre IA analyse votre rapport de durabilité et vous dit exactement ce qui manque.",
        "cta": "Vérifier mon rapport gratuitement",
        "argument": "Idéal pour les PME qui font 1 à 2 rapports par an. Payez à l'analyse, pas au mois.",
    },
    "consultant": {
        "titre": "Consultants : Automatisez vos analyses ESG",
        "sous_titre": "Passez de 2 jours à 3 minutes par rapport client. White-label, export Excel, analyses illimitées.",
        "cta": "Tester gratuitement sur un rapport client",
        "argument": "Le plan Pro vous fait gagner 80% de temps sur vos livrables ESG. Vos clients ne voient que votre marque.",
    },
    "drse": {
        "titre": "Directeurs RSE : Pilotez votre conformité CSRD",
        "sous_titre": "Benchmark sectoriel, suivi pluriannuel, Delta Report pour justifier votre budget en COMEX.",
        "cta": "Analyser mon rapport 2025",
        "argument": "Comparez vos scores aux entreprises de votre secteur. Montrez votre progression année après année.",
    },
    "enterprise": {
        "titre": "Entreprises : Conformité CSRD sécurisée à grande échelle",
        "sous_titre": "SSO, multi-utilisateurs, API, hébergement dédié. Une solution conforme RGPD pour vos équipes.",
        "cta": "Demander une démo personnalisée",
        "argument": "Onboarding dédié, SLA garanti, DPA signé. Vos données restent en Europe.",
    },
}

# Contenu par défaut (générique)
default_content = {
    "titre": "Êtes-vous prêt pour la CSRD ?",
    "sous_titre": "Obtenez votre score ESG en 3 minutes. Notre IA analyse votre rapport de durabilité et génère un diagnostic complet : scores E/S/G, conformité ESRS, recommandations priorisées.",
    "cta": "Analyser mon rapport gratuitement",
    "argument": "Déjà utilisé par des PME, consultants ESG et directeurs RSE pour préparer leur conformité CSRD.",
}

content = PERSONA_CONTENT.get(persona, default_content) if persona else default_content


# ══════════════════════════════════════════════════════════════════
# 1. HERO
# ══════════════════════════════════════════════════════════════════
st.markdown(
    f"""<div style="text-align: center; padding: 50px 20px 30px 20px;">
        <div style="font-size: 48px;">🌿</div>
        <h1 style="margin-top: 10px; color: #111827; font-size: 2.4rem; line-height: 1.2;">
            {content['titre']}
        </h1>
        <p style="font-size: 18px; color: #6B7280; max-width: 700px; margin: 16px auto 0 auto; line-height: 1.6;">
            {content['sous_titre']}
        </p>
    </div>""",
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════
# QUICK-CHECK PUBLIC — Upload sans compte
# ══════════════════════════════════════════════════════════════════
st.markdown(
    """<div style="text-align: center; margin: 10px 0 20px 0;">
        <span style="font-size: 14px; color: #9CA3AF;">ou testez directement ↓</span>
    </div>""",
    unsafe_allow_html=True,
)

qc_col_l, qc_col_center, qc_col_r = st.columns([1, 3, 1])
with qc_col_center:
    uploaded_file = st.file_uploader(
        "Uploadez votre rapport pour un aperçu gratuit",
        type=["pdf", "docx", "xlsx"],
        help="PDF, DOCX ou XLSX — 10 Mo max. Aucun compte requis.",
        key="quick_check_uploader",
    )

    if uploaded_file is not None and "qc_token" not in st.session_state:
        track_quick_check_started()

        with st.spinner("Analyse en cours... (environ 30 secondes)"):
            try:
                file_bytes = uploaded_file.read()
                result = quick_check_upload(file_bytes, uploaded_file.name)
                st.session_state["qc_token"] = result["token"]
            except APIError as e:
                if e.status_code == 429:
                    st.warning(e.detail)
                else:
                    st.error(f"Erreur : {e.detail}")
            except Exception as e:
                st.error(f"Erreur de connexion au serveur : {e}")

    # Polling du résultat si on a un token
    if "qc_token" in st.session_state:
        import time as _time

        token = st.session_state["qc_token"]
        max_polls = 40  # 40 × 3s = 2 minutes max

        if "qc_result" not in st.session_state:
            progress_bar = st.progress(0, text="Extraction du texte...")
            for i in range(max_polls):
                try:
                    qc = quick_check_result(token)
                except Exception:
                    _time.sleep(3)
                    continue

                if qc["status"] == "success":
                    st.session_state["qc_result"] = qc
                    progress_bar.progress(100, text="Analyse terminée !")
                    track_quick_check_completed(qc.get("score_global"))
                    break
                elif qc["status"] == "failed":
                    progress_bar.empty()
                    st.error(f"L'analyse a échoué : {qc.get('error_message', 'Erreur inconnue')}")
                    break
                else:
                    # Progression simulée
                    pct = min(int((i / max_polls) * 95), 95)
                    steps = ["Extraction du texte...", "Analyse IA en cours...",
                             "Scoring ESRS...", "Finalisation..."]
                    step = steps[min(i // 10, 3)]
                    progress_bar.progress(pct, text=step)
                    _time.sleep(3)

        # Affichage du résultat
        if "qc_result" in st.session_state:
            qc = st.session_state["qc_result"]
            score = qc.get("score_global", 0)
            csrd = qc.get("csrd_ready", False)
            strengths = qc.get("teaser_strengths", [])
            weaknesses = qc.get("teaser_weaknesses", [])

            # Score en grand
            score_color = "#10B981" if score >= 60 else "#F59E0B" if score >= 40 else "#EF4444"
            csrd_badge = (
                '<span style="background: #D1FAE5; color: #059669; padding: 4px 12px; '
                'border-radius: 8px; font-weight: 600;">CSRD Ready ✓</span>'
                if csrd else
                '<span style="background: #FEE2E2; color: #DC2626; padding: 4px 12px; '
                'border-radius: 8px; font-weight: 600;">Non conforme ✗</span>'
            )

            st.markdown(
                f"""<div style="text-align: center; padding: 20px; background: #F9FAFB;
                    border-radius: 16px; border: 1px solid #E5E7EB; margin: 16px 0;">
                    <div style="font-size: 56px; font-weight: 800; color: {score_color};">
                        {score}<span style="font-size: 24px; color: #9CA3AF;">/100</span>
                    </div>
                    <div style="margin-top: 8px;">{csrd_badge}</div>
                </div>""",
                unsafe_allow_html=True,
            )

            # Forces et lacunes — visibles mais partiellement floutées
            force_col, weak_col = st.columns(2)
            with force_col:
                st.markdown("**✅ 3 forces détectées**")
                for i, s in enumerate(strengths):
                    if i == 0:
                        st.markdown(f"- {s}")
                    else:
                        # Flou sur les 2 suivantes
                        st.markdown(
                            f'<div style="filter: blur(4px); user-select: none; color: #6B7280;">'
                            f'- {s}</div>',
                            unsafe_allow_html=True,
                        )

            with weak_col:
                st.markdown("**⚠️ 3 lacunes détectées**")
                for i, w in enumerate(weaknesses):
                    if i == 0:
                        st.markdown(f"- {w}")
                    else:
                        st.markdown(
                            f'<div style="filter: blur(4px); user-select: none; color: #6B7280;">'
                            f'- {w}</div>',
                            unsafe_allow_html=True,
                        )

            # CTA massif vers inscription
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                """<div style="text-align: center; background: linear-gradient(135deg, #F0FDF4 0%, #ECFDF5 100%);
                    border: 2px solid #10B981; border-radius: 12px; padding: 20px;">
                    <div style="font-weight: 700; font-size: 16px; color: #111827;">
                        Créez un compte gratuit pour voir le détail
                    </div>
                    <div style="font-size: 13px; color: #6B7280; margin-top: 4px;">
                        10 catégories ESRS • Recommandations priorisées • Rapport PDF complet
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )
            st.page_link(
                "pages/1_Login.py",
                label="Voir le rapport complet — gratuit, 30 secondes",
                icon="🚀",
                use_container_width=True,
            )

            # Bouton reset pour relancer un quick-check
            if st.button("Analyser un autre rapport", use_container_width=True):
                del st.session_state["qc_token"]
                del st.session_state["qc_result"]
                st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# 2. CARDS PERSONA "Je suis..."
# ══════════════════════════════════════════════════════════════════
if not persona:  # N'afficher que sur la landing générique
    st.markdown(
        """<div style="text-align: center; margin-bottom: 8px;">
            <span style="font-size: 14px; color: #9CA3AF; text-transform: uppercase; letter-spacing: 1px;">
                Je suis...
            </span>
        </div>""",
        unsafe_allow_html=True,
    )

    p1, p2, p3, p4 = st.columns(4)

    persona_cards = [
        (p1, "🏢", "PME / ETI", "Préparer ma conformité CSRD", "pme"),
        (p2, "📋", "Consultant ESG", "Gagner du temps sur mes livrables", "consultant"),
        (p3, "🎯", "Directeur RSE", "Piloter ma performance ESG", "drse"),
        (p4, "🏛️", "Entreprise", "Déployer à grande échelle", "enterprise"),
    ]

    for col, icon, title, desc, key in persona_cards:
        with col:
            st.markdown(
                f"""<a href="?persona={key}" style="text-decoration: none; display: block;">
                    <div style="background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 12px;
                        padding: 20px 16px; text-align: center; min-height: 140px; cursor: pointer;
                        transition: border-color 0.2s, box-shadow 0.2s;"
                        onmouseover="this.style.borderColor='#10B981'; this.style.boxShadow='0 2px 8px rgba(16,185,129,0.15)';"
                        onmouseout="this.style.borderColor='#E5E7EB'; this.style.boxShadow='none';">
                        <div style="font-size: 28px;">{icon}</div>
                        <div style="font-weight: 600; font-size: 14px; margin-top: 8px; color: #111827;">
                            {title}
                        </div>
                        <div style="font-size: 12px; color: #6B7280; margin-top: 4px;">
                            {desc}
                        </div>
                        <div style="font-size: 12px; color: #10B981; margin-top: 8px; font-weight: 600;">
                            En savoir plus →
                        </div>
                    </div>
                </a>""",
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

st.divider()

# ══════════════════════════════════════════════════════════════════
# 3. PREUVE SOCIALE (placeholder — à remplir dès 5 users)
# ══════════════════════════════════════════════════════════════════
st.markdown(
    """<div style="text-align: center; padding: 20px 0;">
        <div style="display: flex; justify-content: center; gap: 40px; flex-wrap: wrap;">
            <div>
                <div style="font-size: 28px; font-weight: 700; color: #10B981;">—</div>
                <div style="font-size: 13px; color: #6B7280;">Rapports analysés</div>
            </div>
            <div>
                <div style="font-size: 28px; font-weight: 700; color: #10B981;">—</div>
                <div style="font-size: 13px; color: #6B7280;">Score moyen</div>
            </div>
            <div>
                <div style="font-size: 28px; font-weight: 700; color: #10B981;">3 min</div>
                <div style="font-size: 13px; color: #6B7280;">Temps d'analyse</div>
            </div>
            <div>
                <div style="font-size: 28px; font-weight: 700; color: #10B981;">10</div>
                <div style="font-size: 13px; color: #6B7280;">Standards ESRS couverts</div>
            </div>
        </div>
        <div style="font-size: 12px; color: #9CA3AF; margin-top: 12px;">
            En version beta — rejoignez nos premiers utilisateurs
        </div>
    </div>""",
    unsafe_allow_html=True,
)

st.divider()

# ══════════════════════════════════════════════════════════════════
# 4. COMMENT ÇA MARCHE — 3 étapes
# ══════════════════════════════════════════════════════════════════
st.markdown(
    """<div style="text-align: center; padding: 10px 0 20px 0;">
        <h2 style="color: #111827;">Comment ça marche</h2>
        <p style="color: #6B7280; font-size: 15px;">Un diagnostic ESG complet en 3 étapes simples</p>
    </div>""",
    unsafe_allow_html=True,
)

s1, s2, s3 = st.columns(3)

steps = [
    (s1, "1", "📤", "Uploadez votre rapport",
     "Glissez votre rapport de durabilité (PDF, DOCX ou XLSX). DPEF, rapport RSE, bilan carbone — tout fonctionne."),
    (s2, "2", "🤖", "L'IA analyse en 3 minutes",
     "GPT-4o parcourt votre document, identifie les KPIs, évalue la couverture ESRS et calcule vos scores E/S/G."),
    (s3, "3", "📊", "Recevez votre diagnostic",
     "Score global, conformité CSRD, forces/lacunes, recommandations priorisées et rapport PDF téléchargeable."),
]

for col, num, icon, title, desc in steps:
    with col:
        st.markdown(
            f"""<div style="background: linear-gradient(135deg, #F0FDF4 0%, #ECFDF5 100%);
                border-radius: 12px; padding: 28px 20px; text-align: center; min-height: 220px;">
                <div style="background: #10B981; color: white; width: 32px; height: 32px;
                    border-radius: 50%; display: inline-flex; align-items: center; justify-content: center;
                    font-weight: 700; font-size: 14px; margin-bottom: 12px;">{num}</div>
                <div style="font-size: 32px; margin-bottom: 8px;">{icon}</div>
                <div style="font-weight: 600; font-size: 15px; color: #111827; margin-bottom: 6px;">
                    {title}
                </div>
                <div style="font-size: 13px; color: #6B7280; line-height: 1.5;">
                    {desc}
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)
st.divider()

# ══════════════════════════════════════════════════════════════════
# 5. DÉMO VISUELLE — Aperçu des résultats
# ══════════════════════════════════════════════════════════════════
st.markdown(
    """<div style="text-align: center; padding: 10px 0 20px 0;">
        <h2 style="color: #111827;">Ce que vous obtenez</h2>
        <p style="color: #6B7280; font-size: 15px;">Un rapport complet avec des recommandations actionnables</p>
    </div>""",
    unsafe_allow_html=True,
)

demo_l, demo_r = st.columns(2)

with demo_l:
    st.markdown(
        """<div style="background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 12px; padding: 24px;">
            <div style="font-weight: 600; font-size: 15px; color: #111827; margin-bottom: 12px;">
                📊 Scores ESG détaillés
            </div>
            <div style="display: flex; gap: 12px; margin-bottom: 16px;">
                <div style="flex: 1; background: #D1FAE5; border-radius: 8px; padding: 12px; text-align: center;">
                    <div style="font-size: 24px; font-weight: 700; color: #059669;">72</div>
                    <div style="font-size: 11px; color: #6B7280;">Environnement</div>
                </div>
                <div style="flex: 1; background: #DBEAFE; border-radius: 8px; padding: 12px; text-align: center;">
                    <div style="font-size: 24px; font-weight: 700; color: #2563EB;">65</div>
                    <div style="font-size: 11px; color: #6B7280;">Social</div>
                </div>
                <div style="flex: 1; background: #EDE9FE; border-radius: 8px; padding: 12px; text-align: center;">
                    <div style="font-size: 24px; font-weight: 700; color: #7C3AED;">58</div>
                    <div style="font-size: 11px; color: #6B7280;">Gouvernance</div>
                </div>
            </div>
            <div style="background: white; border-radius: 8px; padding: 12px; border: 1px solid #E5E7EB;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 13px; color: #6B7280;">Score global</span>
                    <span style="font-size: 20px; font-weight: 700; color: #10B981;">65/100</span>
                </div>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

with demo_r:
    st.markdown(
        """<div style="background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 12px; padding: 24px;">
            <div style="font-weight: 600; font-size: 15px; color: #111827; margin-bottom: 12px;">
                📋 Conformité CSRD
            </div>
            <div style="background: #FEF3C7; border-radius: 8px; padding: 12px; margin-bottom: 12px;">
                <div style="font-size: 13px; color: #92400E;">
                    ⚠️ <strong>Partiellement conforme</strong> — Couverture ESRS : 68%
                </div>
            </div>
            <div style="font-size: 13px; color: #374151; margin-bottom: 8px; font-weight: 600;">
                Standards à renforcer :
            </div>
            <div style="font-size: 12px; color: #6B7280; line-height: 1.8;">
                ❌ E1 — Changement climatique<br>
                ❌ S2 — Travailleurs de la chaîne de valeur<br>
                ⚠️ G1 — Gouvernance (partiel)<br>
                ✅ E3 — Eau et ressources marines<br>
                ✅ S1 — Effectifs de l'entreprise
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# Ligne de features complémentaires
f1, f2, f3, f4 = st.columns(4)
features_extra = [
    (f1, "📄", "Rapport PDF", "8 pages téléchargeables"),
    (f2, "📈", "Delta Report", "Évolution année par année"),
    (f3, "💡", "Recommandations", "Priorisées par impact"),
    (f4, "🏆", "Benchmark", "Comparaison sectorielle"),
]
for col, icon, title, desc in features_extra:
    with col:
        st.markdown(
            f"""<div style="text-align: center; padding: 16px 8px;">
                <div style="font-size: 24px;">{icon}</div>
                <div style="font-weight: 600; font-size: 13px; color: #111827; margin-top: 4px;">{title}</div>
                <div style="font-size: 11px; color: #9CA3AF;">{desc}</div>
            </div>""",
            unsafe_allow_html=True,
        )

st.divider()

# ══════════════════════════════════════════════════════════════════
# 6. PRICING — 4 plans
# ══════════════════════════════════════════════════════════════════
track_pricing_viewed(persona)

st.markdown(
    """<div style="text-align: center; padding: 10px 0 20px 0;">
        <h2 style="color: #111827;">Tarifs simples, sans engagement</h2>
        <p style="color: #6B7280; font-size: 15px;">Commencez gratuitement. Passez au supérieur quand vous êtes prêt.</p>
    </div>""",
    unsafe_allow_html=True,
)

pr1, pr2, pr3, pr4 = st.columns(4)

# Plan Découverte
with pr1:
    st.markdown(
        """<div style="background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 12px;
            padding: 24px 16px; text-align: center; min-height: 380px;">
            <div style="font-weight: 700; font-size: 16px; color: #111827;">Découverte</div>
            <div style="font-size: 32px; font-weight: 800; color: #10B981; margin: 12px 0 4px 0;">0 €</div>
            <div style="font-size: 12px; color: #9CA3AF; margin-bottom: 16px;">1 analyse gratuite</div>
            <div style="text-align: left; font-size: 12px; color: #6B7280; line-height: 2;">
                ✅ 1 analyse complète<br>
                ✅ Score global E/S/G<br>
                📄 Rapport PDF (3 pages, watermark)<br>
                ❌ Pas de Delta Report<br>
                ❌ Pas de scores détaillés<br>
                ❌ Historique limité à 1 analyse
            </div>
        </div>""",
        unsafe_allow_html=True,
    )
    st.page_link("pages/1_Login.py", label="Commencer gratuitement", icon="🚀", use_container_width=True)

# Plan Essentiel
with pr2:
    st.markdown(
        """<div style="background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 12px;
            padding: 24px 16px; text-align: center; min-height: 380px;">
            <div style="font-weight: 700; font-size: 16px; color: #111827;">Essentiel</div>
            <div style="font-size: 32px; font-weight: 800; color: #2563EB; margin: 12px 0 4px 0;">39 €</div>
            <div style="font-size: 12px; color: #9CA3AF; margin-bottom: 16px;">par analyse</div>
            <div style="text-align: left; font-size: 12px; color: #6B7280; line-height: 2;">
                ✅ Rapport complet sans watermark<br>
                ✅ Scores E/S/G détaillés<br>
                ✅ Delta Report inclus<br>
                ✅ Conservation 12 mois<br>
                ❌ Pas de benchmark sectoriel<br>
                ❌ Pas de white-label
            </div>
        </div>""",
        unsafe_allow_html=True,
    )
    st.page_link("pages/1_Login.py", label="Acheter une analyse", icon="💳", use_container_width=True)

# Plan Pro (RECOMMANDÉ)
with pr3:
    st.markdown(
        """<div style="background: #F0FDF4; border: 2px solid #10B981; border-radius: 12px;
            padding: 24px 16px; text-align: center; min-height: 380px; position: relative;">
            <div style="position: absolute; top: -12px; left: 50%; transform: translateX(-50%);
                background: #10B981; color: white; padding: 2px 14px; border-radius: 10px;
                font-size: 11px; font-weight: 700;">RECOMMANDÉ</div>
            <div style="font-weight: 700; font-size: 16px; color: #111827; margin-top: 4px;">Pro</div>
            <div style="font-size: 32px; font-weight: 800; color: #10B981; margin: 12px 0 4px 0;">129 €</div>
            <div style="font-size: 12px; color: #9CA3AF; margin-bottom: 16px;">/ mois <span style="color:#10B981;">(ou 990 €/an)</span></div>
            <div style="text-align: left; font-size: 12px; color: #6B7280; line-height: 2;">
                ✅ Analyses illimitées<br>
                ✅ Dashboard complet<br>
                ✅ Benchmark sectoriel<br>
                ✅ Export Excel des KPIs<br>
                ✅ Rapport white-label (votre logo)<br>
                ✅ Historique illimité
            </div>
        </div>""",
        unsafe_allow_html=True,
    )
    st.page_link("pages/1_Login.py", label="Démarrer l'essai Pro", icon="⭐", use_container_width=True)

# Plan Enterprise
with pr4:
    st.markdown(
        """<div style="background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 12px;
            padding: 24px 16px; text-align: center; min-height: 380px;">
            <div style="font-weight: 700; font-size: 16px; color: #111827;">Enterprise</div>
            <div style="font-size: 32px; font-weight: 800; color: #7C3AED; margin: 12px 0 4px 0;">Sur devis</div>
            <div style="font-size: 12px; color: #9CA3AF; margin-bottom: 16px;">adapté à votre organisation</div>
            <div style="text-align: left; font-size: 12px; color: #6B7280; line-height: 2;">
                ✅ Tout le plan Pro<br>
                ✅ SSO / SAML<br>
                ✅ Multi-utilisateurs<br>
                ✅ Accès API<br>
                ✅ SLA garanti<br>
                ✅ Formation & onboarding
            </div>
        </div>""",
        unsafe_allow_html=True,
    )
    # Bouton "Nous contacter" — ouvre un mailto ou Calendly (à configurer sprint 6D)
    st.link_button("Nous contacter", "mailto:diadamflow@gmail.com?subject=ESG%20Optimizer%20Enterprise", icon="📧", use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════
# 7. FAQ
# ══════════════════════════════════════════════════════════════════
st.markdown(
    """<div style="text-align: center; padding: 10px 0 20px 0;">
        <h2 style="color: #111827;">Questions fréquentes</h2>
    </div>""",
    unsafe_allow_html=True,
)

with st.expander("🔒 Mes données sont-elles en sécurité ?"):
    st.write(
        "Oui. Vos rapports sont traités via des serveurs européens. Les données sont chiffrées "
        "en transit (HTTPS) et au repos. Nous ne partageons jamais vos documents avec des tiers. "
        "L'API OpenAI est configurée pour ne **pas** utiliser vos données à des fins d'entraînement "
        "(header `x-openai-skip-training`)."
    )

with st.expander("📋 Qu'est-ce que la CSRD et suis-je concerné ?"):
    st.write(
        "La Corporate Sustainability Reporting Directive (CSRD) est la directive européenne qui "
        "oblige les entreprises à publier un rapport de durabilité conforme aux standards ESRS. "
        "Depuis 2025, elle s'applique aux grandes entreprises ; en 2026, aux PME cotées. "
        "Si vous avez un doute, notre analyse gratuite vous dira immédiatement si votre rapport "
        "est conforme."
    )

with st.expander("🤖 Quelle IA est utilisée ? Est-elle fiable ?"):
    st.write(
        "Nous utilisons GPT-4o d'OpenAI, le modèle le plus performant pour l'analyse de texte. "
        "Notre système prompt est calibré sur les 10 standards ESRS (E1-E5, S1-S4, G1) et produit "
        "des scores reproductibles (température 0.2). L'IA identifie les KPIs, évalue la couverture "
        "et génère des recommandations — mais ne remplace pas un auditeur. C'est un outil d'aide "
        "à la décision."
    )

with st.expander("📄 Quels formats de rapport acceptez-vous ?"):
    st.write(
        "PDF, DOCX et XLSX. Tous les types de rapports de durabilité fonctionnent : DPEF, rapport "
        "RSE, rapport annuel avec section ESG, bilan carbone, rapport intégré. La taille maximale "
        "est de 20 Mo."
    )

with st.expander("💰 Le plan Découverte est-il vraiment gratuit ?"):
    st.write(
        "Oui, 100% gratuit, sans carte bancaire. Vous obtenez 1 analyse complète avec un score "
        "global et un aperçu du rapport PDF (3 pages sur 8). Pour accéder au rapport complet, "
        "aux scores détaillés et au Delta Report, passez au plan Essentiel (39 €/analyse) ou Pro."
    )

with st.expander("📊 Qu'est-ce que le Delta Report ?"):
    st.write(
        "Le Delta Report compare votre rapport actuel avec celui de l'année précédente (même "
        "entreprise). Il montre l'évolution de chaque score, les KPIs améliorés/dégradés, "
        "et les standards ESRS gagnés ou perdus. C'est un outil puissant pour les DRSE qui "
        "doivent justifier leur progression devant le COMEX."
    )

with st.expander("🗑️ Puis-je supprimer mes données ?"):
    st.write(
        "Oui. Conformément au RGPD, vous pouvez demander la suppression complète de votre compte "
        "et de toutes vos données (rapports, analyses, résultats) à tout moment. Un endpoint "
        "dédié (`DELETE /users/me`) sera disponible, ou contactez-nous par email."
    )

with st.expander("🏷️ Le rapport white-label fonctionne comment ?"):
    st.write(
        "Avec le plan Pro, vous pouvez remplacer le logo ESG Optimizer par le logo de votre "
        "cabinet ou de votre entreprise sur le rapport PDF. Idéal pour les consultants qui "
        "livrent des analyses à leurs clients sous leur propre marque."
    )

st.divider()

# ══════════════════════════════════════════════════════════════════
# 8. CTA FINAL
# ══════════════════════════════════════════════════════════════════
st.markdown(
    """<div style="text-align: center; padding: 30px 20px;">
        <h2 style="color: #111827;">Prêt à analyser votre rapport ESG ?</h2>
        <p style="color: #6B7280; font-size: 15px;">
            Gratuit, sans engagement, résultat en 3 minutes.
        </p>
    </div>""",
    unsafe_allow_html=True,
)

col_l2, col_cta2, col_r2 = st.columns([1, 2, 1])
with col_cta2:
    if is_logged_in():
        st.page_link("pages/2_Upload.py", label="Lancer mon analyse gratuite", icon="🚀", use_container_width=True)
    else:
        st.page_link("pages/1_Login.py", label="Créer mon compte gratuitement", icon="🚀", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# 9. FOOTER
# ══════════════════════════════════════════════════════════════════
st.markdown(
    """<div style="border-top: 1px solid #E5E7EB; padding: 30px 20px; margin-top: 20px;">
        <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 16px;
            max-width: 800px; margin: 0 auto;">
            <div>
                <div style="font-weight: 700; color: #10B981; font-size: 16px;">ESG Optimizer AI</div>
                <div style="font-size: 12px; color: #9CA3AF; margin-top: 4px;">
                    Analyse ESG automatisée par IA
                </div>
            </div>
            <div style="font-size: 12px; color: #9CA3AF; line-height: 2;">
                <a href="#" style="color: #6B7280; text-decoration: none;">Mentions légales</a><br>
                <a href="#" style="color: #6B7280; text-decoration: none;">CGU</a><br>
                <a href="#" style="color: #6B7280; text-decoration: none;">Politique de confidentialité</a>
            </div>
            <div style="font-size: 12px; color: #9CA3AF; line-height: 2;">
                <a href="mailto:diadamflow@gmail.com" style="color: #6B7280; text-decoration: none;">Contact</a><br>
                Conforme ESRS E1-E5, S1-S4, G1<br>
                Hébergement UE 🇪🇺
            </div>
        </div>
        <div style="text-align: center; font-size: 11px; color: #D1D5DB; margin-top: 20px;">
            © 2026 ESG Optimizer AI — Tous droits réservés
        </div>
    </div>""",
    unsafe_allow_html=True,
)
