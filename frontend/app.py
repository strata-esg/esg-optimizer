"""
ESG Optimizer MVP — Point d'entrée Streamlit.
Lancer avec : cd frontend && streamlit run app.py --server.port 8501
"""

import streamlit as st

# ── Configuration de la page (DOIT être le premier appel Streamlit) ──
st.set_page_config(
    page_title="ESG Optimizer AI",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Import après set_page_config ─────────────────────────────────
import sys
from pathlib import Path

# Ajouter le dossier parent au path pour que les imports relatifs fonctionnent
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from frontend.components.sidebar import render_sidebar
from frontend.components.analytics import inject_umami_script
from frontend.utils.session import is_logged_in

# ── Sidebar ──────────────────────────────────────────────────────
render_sidebar()

# ── Analytics Umami ──────────────────────────────────────────────
inject_umami_script()

# ── Page d'accueil ───────────────────────────────────────────────
st.markdown(
    """<div style="text-align: center; padding: 60px 20px 40px 20px;">
        <div style="font-size: 48px;">🌿</div>
        <h1 style="margin-top: 10px; color: #111827;">ESG Optimizer AI</h1>
        <p style="font-size: 18px; color: #6B7280; max-width: 600px; margin: 10px auto;">
            Analysez vos rapports de durabilité en quelques minutes.<br>
            Scores ESG, conformité CSRD, recommandations ESRS — automatiquement.
        </p>
    </div>""",
    unsafe_allow_html=True,
)

if is_logged_in():
    # Utilisateur connecté — raccourcis vers les pages principales
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            """<div style="background: #F0FDF4; border-radius: 12px; padding: 24px; text-align: center;">
                <div style="font-size: 36px;">📤</div>
                <div style="font-weight: 600; margin-top: 8px;">Nouvelle Analyse</div>
                <div style="font-size: 13px; color: #6B7280; margin-top: 4px;">
                    Uploadez un rapport PDF, DOCX ou XLSX
                </div>
            </div>""",
            unsafe_allow_html=True,
        )
        st.page_link("pages/2_Upload.py", label="Lancer une analyse", icon="📤", use_container_width=True)

    with col2:
        st.markdown(
            """<div style="background: #EFF6FF; border-radius: 12px; padding: 24px; text-align: center;">
                <div style="font-size: 36px;">📊</div>
                <div style="font-weight: 600; margin-top: 8px;">Résultats</div>
                <div style="font-size: 13px; color: #6B7280; margin-top: 4px;">
                    Consultez votre dernière analyse ESG
                </div>
            </div>""",
            unsafe_allow_html=True,
        )
        st.page_link("pages/3_Resultats.py", label="Voir les résultats", icon="📊", use_container_width=True)

    with col3:
        st.markdown(
            """<div style="background: #FDF2F8; border-radius: 12px; padding: 24px; text-align: center;">
                <div style="font-size: 36px;">📈</div>
                <div style="font-weight: 600; margin-top: 8px;">Dashboard</div>
                <div style="font-size: 13px; color: #6B7280; margin-top: 4px;">
                    Historique et tendances ESG
                </div>
            </div>""",
            unsafe_allow_html=True,
        )
        st.page_link("pages/4_Dashboard.py", label="Ouvrir le dashboard", icon="📈", use_container_width=True)
else:
    # Non connecté — inviter à se connecter
    st.markdown(
        """<div style="text-align: center; margin-top: 20px;">
            <p style="color: #6B7280;">Connectez-vous pour commencer votre première analyse ESG.</p>
        </div>""",
        unsafe_allow_html=True,
    )
    col_left, col_center, col_right = st.columns([1, 1, 1])
    with col_center:
        st.page_link("pages/1_Login.py", label="Se connecter / S'inscrire", icon="🔐", use_container_width=True)
