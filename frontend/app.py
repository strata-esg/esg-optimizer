"""
ESG Optimizer — Point d'entree Streamlit.
Lancer avec : cd frontend && streamlit run app.py --server.port 8501
"""

import sys
from pathlib import Path

import streamlit as st

# Config page (doit etre le premier appel Streamlit)
st.set_page_config(
    page_title="ESG Optimizer",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Path setup
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from frontend.components.sidebar import render_sidebar
from frontend.components.analytics import inject_umami_script
from frontend.utils.styles import inject_global_styles

# Styles brand
inject_global_styles()

# Pages
pages = [
    st.Page("pages/0_Accueil.py",    title="Accueil",           icon="🌿", default=True),
    st.Page("pages/1_Login.py",      title="Connexion",         icon="🔐"),
    st.Page("pages/2_Upload.py",     title="Upload",            icon="📤"),
    st.Page("pages/3_Resultats.py",  title="Résultats",         icon="📊"),
    st.Page("pages/4_Dashboard.py",  title="Dashboard",         icon="📈"),
    st.Page("pages/5_Parametres.py", title="Paramètres",        icon="⚙️"),
    st.Page("pages/6_Tarifs.py",     title="Tarifs",            icon="💳"),
    st.Page("pages/7_Mentions.py",   title="Mentions & Méthodo", icon="📋"),
]

pg = st.navigation(pages, position="hidden")

# Sidebar + Analytics (toutes les pages)
render_sidebar()
inject_umami_script()

pg.run()
