"""
ESG Optimizer MVP — Page Paramètres.
Profil utilisateur, abonnement, préférences email, zone avancée.
"""

import streamlit as st
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from frontend.utils.api_client import APIError, get_me, get_email_preferences, update_email_preferences
from frontend.utils.session import get_token, get_user, save_user, require_auth

if not require_auth():
    st.stop()

token = get_token()

# Charger les infos utilisateur fraîches
try:
    user = get_me(token)
    save_user(user)
except APIError as e:
    st.error(f"Erreur : {e.detail}")
    user = get_user() or {}
except Exception:
    user = get_user() or {}

# Header
st.markdown(
    """<div style="padding: 10px 0 20px 0;">
        <h2>Paramètres</h2>
        <p style="color: #6B7280;">Gérez votre profil, abonnement et notifications.</p>
    </div>""",
    unsafe_allow_html=True,
)

# 1. PROFIL
st.subheader("Profil")

col1, col2 = st.columns(2)
with col1:
    st.text_input("Email", value=user.get("email", ""), disabled=True)
with col2:
    st.text_input("Entreprise", value=user.get("company_name", "") or "Non renseignée", disabled=True)

st.caption(
    f"Compte créé le {user.get('created_at', '?')[:10] if user.get('created_at') else '?'}"
)

# 2. ABONNEMENT
st.markdown('<div style="height:1px;background:linear-gradient(90deg,transparent,#D1D5DB 25%,#D1D5DB 75%,transparent);margin:20px 0;"></div>', unsafe_allow_html=True)
st.subheader("Abonnement")

plan = user.get("plan", "discovery")
analyses_month = user.get("analyses_this_month", 0)

plan_display = {
    "discovery": ("Découverte", "#E5E7EB", "#374151"),
    "free": ("Découverte", "#E5E7EB", "#374151"),
    "essential": ("Essentiel", "#DBEAFE", "#2563EB"),
    "pro": ("Pro", "#D4F0D8", "#1A3D22"),
    "enterprise": ("Enterprise", "#EDE9FE", "#7C3AED"),
}

label, bg, color = plan_display.get(plan, plan_display["discovery"])

if plan in ("pro", "enterprise"):
    st.markdown(
        f"""<div style="background: {bg}; border: 2px solid {color}; border-radius: 12px;
            padding: 24px;">
            <div style="font-weight: 700; color: {color}; font-size: 20px;">
                Plan {label} &#10003;
            </div>
            <div style="color: {color}; margin-top: 8px;">
                Analyses illimitées. Merci pour votre confiance !
            </div>
        </div>""",
        unsafe_allow_html=True,
    )
    st.metric("Analyses ce mois", analyses_month)
elif plan == "essential":
    st.markdown(
        f"""<div style="background: {bg}; border: 2px solid {color}; border-radius: 12px;
            padding: 24px;">
            <div style="font-weight: 700; color: {color}; font-size: 20px;">
                Plan {label}
            </div>
            <div style="color: #6B7280; margin-top: 8px;">
                Analyses à l'unité (39€/analyse). {analyses_month} analyse(s) réalisée(s).
            </div>
        </div>""",
        unsafe_allow_html=True,
    )
else:
    remaining = max(0, 1 - analyses_month)
    st.markdown(
        f"""<div style="background: #F9FAFB; border: 2px solid #E5E7EB; border-radius: 12px;
            padding: 24px;">
            <div style="font-weight: 700; color: #374151; font-size: 20px;">
                Plan Découverte
            </div>
            <div style="color: #6B7280; margin-top: 8px;">
                {remaining} analyse gratuite restante sur 1
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

if plan in ("discovery", "free", "essential"):
    st.markdown("")
    if st.button("Voir les tarifs et upgrader", use_container_width=True, type="primary"):
        st.switch_page("pages/6_Tarifs.py")

# 3. PRÉFÉRENCES EMAIL
st.markdown('<div style="height:1px;background:linear-gradient(90deg,transparent,#D1D5DB 25%,#D1D5DB 75%,transparent);margin:20px 0;"></div>', unsafe_allow_html=True)
st.subheader("Notifications email")

# Charger les préférences actuelles
try:
    prefs = get_email_preferences(token)
    current_notif = prefs.get("email_notifications", True)
except Exception:
    current_notif = True

st.markdown(
    """<p style="color: #6B7280; font-size: 14px;">
        Contrôlez les emails que vous recevez d'ESG Optimizer.
    </p>""",
    unsafe_allow_html=True,
)

new_notif = st.toggle(
    "Recevoir les notifications par email",
    value=current_notif,
    help="Inclut : résultats d'analyse, digest hebdomadaire, confirmations de paiement.",
)

if new_notif != current_notif:
    try:
        update_email_preferences(token, new_notif)
        state_text = "activées" if new_notif else "désactivées"
        st.success(f"Notifications email {state_text}.")
    except APIError as e:
        st.error(f"Erreur : {e.detail}")

st.caption(
    "Même avec les notifications désactivées, vous recevrez toujours "
    "les emails de sécurité (changement de mot de passe, etc.)."
)

# 4. ZONE AVANCÉE
st.markdown('<div style="