"""
ESG Optimizer — Point d'entree Streamlit.
Lancer avec : cd frontend && streamlit run app.py --server.port 8501
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

import streamlit as st
from PIL import Image

# Config page (doit etre le premier appel Streamlit)
_root = Path(__file__).resolve().parent.parent
_favicon = Image.open(_root / "frontend" / "static" / "brand" / "favicon.png")

st.set_page_config(
    page_title="ESG Optimizer — Analyse IA & Conformité CSRD",
    page_icon=_favicon,
    layout="wide",
    initial_sidebar_state="expanded",
)

# Path setup
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from frontend.components.sidebar import render_sidebar
from frontend.components.analytics import inject_umami_script
from frontend.utils.styles import inject_global_styles
from frontend.utils.session import get_token, save_token, save_user, clear_token, clear_user

# Styles brand
inject_global_styles()

# ── Cookie manager — persistence de session entre les refreshs ────────────────
try:
    import extra_streamlit_components as stx
    _cm = stx.CookieManager(key="esg_cm")
    # Stocker dans session_state pour que les pages puissent l'utiliser
    st.session_state["_cm"] = _cm

    # Restaurer la session depuis le cookie si la page a été rafraîchie
    if not get_token() and not st.session_state.get("_cookie_checked"):
        st.session_state["_cookie_checked"] = True
        _jwt = _cm.get("esg_jwt")
        if _jwt:
            try:
                from frontend.utils.api_client import get_me
                _user = get_me(_jwt)
                save_token(_jwt)
                save_user(_user)
                st.rerun()
            except Exception:
                # Token expiré ou invalide — supprimer le cookie
                _cm.delete("esg_jwt")
except Exception:
    pass  # Package non dispo en dev local sans pip install

# ── Pages ─────────────────────────────────────────────────────────────────────
pages = [
    st.Page("pages/0_Accueil.py",    title="Accueil",            default=True),
    st.Page("pages/1_Login.py",      title="Connexion"),
    st.Page("pages/2_Upload.py",     title="Upload"),
    st.Page("pages/3_Resultats.py",  title="Résultats"),
    st.Page("pages/4_Dashboard.py",  title="Dashboard"),
    st.Page("pages/5_Parametres.py", title="Paramètres"),
    st.Page("pages/6_Tarifs.py",     title="Tarifs"),
    st.Page("pages/7_Mentions.py",   title="Mentions & Méthodo"),
]

pg = st.navigation(pages, position="hidden")

# Sidebar + Analytics (toutes les pages)
render_sidebar()
inject_umami_script()

pg.run()
