"""
ESG Optimizer MVP — Page Paramètres.
Profil utilisateur, plan, compteur d'analyses, placeholder upgrade.
"""

import streamlit as st
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from frontend.components.sidebar import render_sidebar
from frontend.utils.api_client import APIError, get_me
from frontend.utils.session import get_token, get_user, save_user, require_auth

# ── Config page ──────────────────────────────────────────────────
st.set_page_config(page_title="Paramètres — ESG Optimizer", page_icon="⚙️", layout="centered")
render_sidebar()

if not require_auth():
    st.stop()

token = get_token()

# ── Charger les infos utilisateur fraîches ───────────────────────
try:
    user = get_me(token)
    save_user(user)
except APIError as e:
    st.error(f"Erreur : {e.detail}")
    user = get_user() or {}
except Exception:
    user = get_user() or {}

# ── Header ───────────────────────────────────────────────────────
st.markdown(
    """<div style="padding: 10px 0 20px 0;">
        <h2>⚙️ Paramètres</h2>
        <p style="color: #6B7280;">Gérez votre profil et votre abonnement.</p>
    </div>""",
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════
# 1. PROFIL
# ══════════════════════════════════════════════════════════════════
st.subheader("Profil")

col1, col2 = st.columns(2)
with col1:
    st.text_input("Email", value=user.get("email", ""), disabled=True)
with col2:
    st.text_input("Entreprise", value=user.get("company_name", "") or "Non renseignée", disabled=True)

st.caption(
    f"Compte créé le {user.get('created_at', '?')[:10] if user.get('created_at') else '?'}"
)

# ══════════════════════════════════════════════════════════════════
# 2. ABONNEMENT
# ══════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("Abonnement")

plan = user.get("plan", "free")
analyses_month = user.get("analyses_this_month", 0)

if plan == "pro":
    st.markdown(
        """<div style="background: #D1FAE5; border: 2px solid #10B981; border-radius: 12px;
            padding: 24px;">
            <div style="font-weight: 700; color: #065F46; font-size: 20px;">
                Plan Pro &#10003;
            </div>
            <div style="color: #065F46; margin-top: 8px;">
                Analyses illimitées. Merci pour votre confiance !
            </div>
        </div>""",
        unsafe_allow_html=True,
    )
    st.metric("Analyses ce mois", analyses_month)
else:
    st.markdown(
        f"""<div style="background: #F9FAFB; border: 2px solid #E5E7EB; border-radius: 12px;
            padding: 24px;">
            <div style="font-weight: 700; color: #374151; font-size: 20px;">
                Plan Gratuit
            </div>
            <div style="color: #6B7280; margin-top: 8px;">
                {analyses_month}/1 analyse(s) utilisée(s) ce mois
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    st.markdown("")

    # ── Comparaison plans ────────────────────────────────
    col_free, col_pro = st.columns(2)

    with col_free:
        st.markdown(
            """<div style="border: 1px solid #E5E7EB; border-radius: 12px; padding: 20px;">
                <div style="font-weight: 700; font-size: 18px;">Gratuit</div>
                <div style="font-size: 28px; font-weight: 700; margin: 12px 0;">0€</div>
                <div style="font-size: 13px; color: #6B7280;">
                    &#10003; 1 analyse / mois<br>
                    &#10003; Scores E/S/G<br>
                    &#10003; Rapport PDF<br>
                    &#10007; Delta Report<br>
                    &#10007; Analyses illimitées
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

    with col_pro:
        st.markdown(
            """<div style="border: 2px solid #10B981; border-radius: 12px; padding: 20px;
                background: #F0FDF4;">
                <div style="font-weight: 700; font-size: 18px; color: #065F46;">Pro</div>
                <div style="font-size: 28px; font-weight: 700; margin: 12px 0; color: #065F46;">
                    49€<span style="font-size: 14px; font-weight: 400;">/mois</span>
                </div>
                <div style="font-size: 13px; color: #065F46;">
                    &#10003; Analyses illimitées<br>
                    &#10003; Scores E/S/G<br>
                    &#10003; Rapport PDF<br>
                    &#10003; Delta Report<br>
                    &#10003; Support prioritaire
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("")
    if st.button("Passer en Pro", use_container_width=True, type="primary"):
        st.info(
            "Le paiement en ligne arrive bientôt ! "
            "Contactez-nous à contact@esgoptimizer.ai pour activer votre plan Pro."
        )

# ══════════════════════════════════════════════════════════════════
# 3. DANGER ZONE (placeholder)
# ══════════════════════════════════════════════════════════════════
st.markdown("---")
with st.expander("Zone avancée"):
    st.caption("Ces fonctionnalités seront disponibles dans une prochaine version.")
    st.button("Modifier mon mot de passe", disabled=True, use_container_width=True)
    st.button("Supprimer mon compte", disabled=True, use_container_width=True, type="secondary")
