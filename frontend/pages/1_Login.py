"""
ESG Optimizer MVP — Page Login / Register.
Design split-panel : panneau gauche brand vert + formulaire droit crème.
"""

import streamlit as st
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from frontend.utils.api_client import APIError, login, register, get_me
from frontend.utils.session import is_logged_in, save_token, save_user
from frontend.components.onboarding import render_onboarding

# ── Guard : déjà connecté (AVANT le CSS split-panel pour éviter les conflits) ─
# Le CSS split-panel cible [data-testid="column"]:first-child de façon globale.
# Si l'onboarding est rendu avec ce CSS actif, ses propres st.columns() héritent
# du fond vert foncé. En plaçant ce guard avant l'injection CSS, le CSS
# n'est jamais présent quand l'onboarding tourne.
if is_logged_in():
    if st.session_state.get("show_onboarding"):
        done = render_onboarding()
        if not done:
            st.stop()
        st.session_state.pop("show_onboarding", None)
    st.switch_page("pages/0_Accueil.py")
    st.stop()

# ── CSS split-panel (injecté seulement pour le formulaire login/register) ─────
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&display=swap');

    /* Désactiver le padding par défaut */
    .block-container {{
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        max-width: 100% !important;
    }}
    .stApp > header {{ display: none !important; }}

    /* Panneau gauche (1ère colonne) */
    [data-testid="column"]:first-child > div:first-child {{
        background: #1B3D20 !important;
        min-height: 100vh !important;
        padding: 48px 40px !important;
        border-radius: 0 !important;
    }}
    [data-testid="column"]:first-child p,
    [data-testid="column"]:first-child span,
    [data-testid="column"]:first-child div,
    [data-testid="column"]:first-child label {{
        color: rgba(255,255,255,0.85) !important;
    }}

    /* Panneau droit */
    [data-testid="column"]:last-child > div:first-child {{
        background: #F7F2E8 !important;
        min-height: 100vh !important;
        padding: 48px 48px !important;
    }}

    /* Formulaire */
    .esg-login-form .stTextInput > div > div > input {{
        background: #FFFFFF !important;
        border: 1.5px solid #E5E7EB !important;
        border-radius: 10px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 15px !important;
        padding: 12px 14px !important;
        color: #1A1A1A !important;
    }}
    .esg-login-form .stTextInput > div > div > input:focus {{
        border-color: #1B3D20 !important;
        box-shadow: 0 0 0 3px rgba(27,61,32,0.1) !important;
    }}
    .esg-login-form .stButton > button[kind="primary"] {{
        background: #4DB862 !important;
        color: #1B3D20 !important;
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        border-radius: 10px !important;
        border: none !important;
        padding: 12px 24px !important;
        width: 100% !important;
        transition: all 0.15s ease !important;
    }}
    .esg-login-form .stButton > button[kind="primary"]:hover {{
        background: #3A7D3C !important;
        box-shadow: 0 4px 12px rgba(27,61,32,0.25) !important;
        transform: translateY(-1px) !important;
    }}
    .esg-form-toggle .stRadio label span {{
        color: #6B7280 !important;
        font-family: 'DM Sans', sans-serif !important;
    }}
    </style>

    <style>
    /* Logo dans le panneau gauche */
    .esg-brand-logo {{ width: 160px; margin-bottom: 32px; }}
    .esg-brand-logo svg {{ width: 100%; height: auto; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Layout split-panel ───────────────────────────────────────────────────────
col_left, col_right = st.columns([4, 5], gap="small")

# ── Panneau gauche : brand ───────────────────────────────────────────────────
with col_left:
    st.markdown(
        """
        <div style="font-family:'DM Serif Display',Georgia,serif; font-size:2.2rem;
            font-weight:400; line-height:1.2; color:#FFFFFF; margin-bottom:16px;
            letter-spacing:-0.02em;">
            Votre score ESG<br>en 3 minutes.
        </div>
        <div style="font-family:'DM Sans',sans-serif; font-size:14px; color:rgba(255,255,255,0.7);
            line-height:1.65; margin-bottom:40px; max-width:320px;">
            Analyse IA de vos rapports de durabilité. Scores E/S/G,
            conformité ESRS, recommandations priorisées.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Features list
    features = [
        ("✦", "Score global E/S/G instantané"),
        ("✦", "Couverture ESRS (10 standards)"),
        ("✦", "Rapport PDF téléchargeable"),
        ("✦", "Delta Report année/année"),
    ]
    for icon, text in features:
        st.markdown(
            f'<div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">'
            f'<span style="color:#4DB862; font-size:14px;">{icon}</span>'
            f'<span style="font-family:\'DM Sans\',sans-serif; font-size:14px; color:rgba(255,255,255,0.8);">{text}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ── Panneau droit : formulaire ───────────────────────────────────────────────
with col_right:
    st.markdown("<div style='height: 48px'></div>", unsafe_allow_html=True)

    # Toggle connexion / inscription
    mode = st.radio(
        "Mode",
        ["Se connecter", "S'inscrire"],
        horizontal=True,
        label_visibility="collapsed",
        key="login_mode_toggle",
    )
    is_register = mode == "S'inscrire"

    st.markdown(
        f"""
        <div style="margin-bottom:28px; margin-top:8px;">
            <div style="font-family:'DM Serif Display',Georgia,serif; font-size:1.9rem;
                font-weight:400; color:#1A1A1A; letter-spacing:-0.02em;">
                {'Créer un compte' if is_register else 'Se connecter'}
            </div>
            <div style="font-family:'DM Sans',sans-serif; font-size:14px; color:#6B7280; margin-top:4px;">
                {'Rejoignez ESG Optimizer gratuitement' if is_register else 'Accédez à votre espace ESG'}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="esg-login-form">', unsafe_allow_html=True)

    with st.form("auth_form", clear_on_submit=False):
        lbl_email = "Email professionnel" if is_register else "Email"
        email = st.text_input(lbl_email, placeholder="vous@entreprise.fr", label_visibility="visible")
        password = st.text_input(
            "Mot de passe",
            type="password",
            placeholder="8 caractères minimum" if is_register else "Votre mot de passe",
        )
        company_name = None
        if is_register:
            company_name = st.text_input(
                "Nom de votre entreprise (optionnel)",
                placeholder="Ex : GreenTech SAS",
            )

        submitted = st.form_submit_button(
            "Créer mon compte →" if is_register else "Se connecter →",
            use_container_width=True,
            type="primary",
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Traitement ────────────────────────────────────────────────────────────
    if submitted:
        if not email or not password:
            st.error("Veuillez remplir l'email et le mot de passe.")
            st.stop()
        if is_register and len(password) < 8:
            st.error("Le mot de passe doit contenir au moins 8 caractères.")
            st.stop()

        try:
            with st.spinner("Connexion en cours..." if not is_register else "Création du compte..."):
                if is_register:
                    result = register(email, password, company_name or None)
                    token = result["access_token"]
                    save_token(token)
                    user_data = result.get("user") or get_me(token)
                    save_user(user_data)
                    st.session_state["show_onboarding"] = True
                    st.success("Compte créé ! Bienvenue 🎉")
                    st.balloons()
                    st.rerun()
                else:
                    result = login(email, password)
                    token = result["access_token"]
                    save_token(token)
                    save_user(get_me(token))
                    st.success("Connexion réussie !")
                    st.balloons()
                    st.switch_page("pages/0_Accueil.py")

        except APIError as e:
            if e.status_code == 401:
                st.error("Email ou mot de passe incorrect.")
            elif e.status_code == 409:
                st.error("Cette adresse email est déjà utilisée. Connectez-vous ou utilisez une autre adresse.")
            elif e.status_code == 422:
                st.error("Informations invalides. Vérifiez votre email et mot de passe.")
            elif e.status_code == 429:
                st.error("Trop de tentatives. Patientez quelques minutes.")
            else:
                st.error(f"Erreur : {e.detail}")
        except Exception:
            st.error("Impossible de contacter le serveur. Vérifiez votre connexion.")

    # ── Lien mot de passe oublié + inscription ───────────────────────────────
    # Note : pas de backslash dans une expression f-string (Python 3.11)
    if is_register:
        _toggle_link = (
            'Déjà un compte ? <a href="?mode=login" style="color:#B45309; font-weight:500; '
            'text-decoration:none;">Se connecter</a>'
        )
    else:
        _toggle_link = (
            "Pas encore de compte ? <a href=\"?mode=register\" style=\"color:#B45309; "
            "font-weight:500; text-decoration:none;\">S'inscrire</a>"
        )

    st.markdown(
        f"""
        <div style="margin-top:20px; text-align:center; font-family:'DM Sans',sans-serif;
            font-size:13px; color:#6B7280;">
            {_toggle_link}
        </div>
        """,
        unsafe_allow_html=True,
    )
