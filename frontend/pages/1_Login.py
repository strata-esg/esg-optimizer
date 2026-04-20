"""
ESG Optimizer MVP — Page Login / Register.
Formulaire email + mot de passe avec toggle inscription/connexion.
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

# Si déjà connecté, vérifier onboarding
if is_logged_in():
    if st.session_state.get("show_onboarding"):
        done = render_onboarding()
        if not done:
            st.stop()
        st.session_state.pop("show_onboarding", None)
    st.success("Vous êtes déjà connecté !")
    st.page_link("pages/2_Upload.py", label="Aller à l'upload")
    st.stop()

# Header
st.markdown(
    """<div style="text-align: center; padding: 20px 0;">
        <h2>Connexion</h2>
        <p style="color: #6B7280;">Accédez à votre espace ESG Optimizer</p>
    </div>""",
    unsafe_allow_html=True,
)

# Toggle inscription / connexion
mode = st.radio(
    "Mode",
    ["Se connecter", "Créer un compte"],
    horizontal=True,
    label_visibility="collapsed",
)

is_register = mode == "Créer un compte"

# Formulaire
with st.form("auth_form"):
    email = st.text_input("Email", placeholder="vous@entreprise.com")
    password = st.text_input("Mot de passe", type="password", placeholder="8 caractères minimum")

    company_name = None
    if is_register:
        company_name = st.text_input(
            "Nom de votre entreprise (optionnel)",
            placeholder="Ex: GreenTech SAS",
        )

    submitted = st.form_submit_button(
        "Créer mon compte" if is_register else "Se connecter",
        use_container_width=True,
        type="primary",
    )

# Traitement du formulaire
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
                user_data = result.get("user")
                if user_data:
                    save_user(user_data)
                else:
                    save_user(get_me(token))
                st.session_state["show_onboarding"] = True
                st.success("Compte créé avec succès !")
            else:
                result = login(email, password)
                token = result["access_token"]
                save_token(token)
                # Charger les infos user
                user_data = get_me(token)
                save_user(user_data)
                st.success("Connexion réussie !")

            st.balloons()
            st.page_link("pages/2_Upload.py", label="Commencer une analyse")
            st.rerun()

    except APIError as e:
        st.error(f"Erreur : {e.detail}")
    except Exception as e:
        st.error(f"Erreur de connexion au serveur : {e}")
