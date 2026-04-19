"""
Système de styles ESG Optimizer.
Polices DM Serif Display + DM Sans, palette brand, overrides Streamlit.
"""

import streamlit as st

COLORS = {
    "forest":      "#1A3D22",
    "forest_mid":  "#2A5C34",
    "leaf":        "#7FC686",
    "mint":        "#D4F0D8",
    "parchment":   "#F5F2EC",
    "amber":       "#C17B2A",
    "amber_light": "#FDF3E3",
    "alert":       "#B53030",
    "alert_light": "#FDF0F0",
    "text":        "#1C1C1C",
    "text_muted":  "#6B7280",
    "border":      "#E5E0D8",
    "white":       "#FFFFFF",
}


def inject_global_styles() -> None:
    """Charge les polices Google Fonts et applique le thème brand."""
    st.markdown(
        """
        <link
          href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&family=DM+Serif+Display:ital@0;1&display=swap"
          rel="stylesheet"
        />

        <style>
        :root {
          --esg-forest:      #1A3D22;
          --esg-forest-mid:  #2A5C34;
          --esg-leaf:        #7FC686;
          --esg-mint:        #D4F0D8;
          --esg-parchment:   #F5F2EC;
          --esg-amber:       #C17B2A;
          --esg-amber-light: #FDF3E3;
          --esg-alert:       #B53030;
          --esg-alert-light: #FDF0F0;
          --esg-text:        #1C1C1C;
          --esg-text-muted:  #6B7280;
          --esg-border:      #E5E0D8;
        }

        /* Typographie */
        html, body, [class*="css"], p, span, div, label, li {
          font-family: 'DM Sans', system-ui, -apple-system, sans-serif !important;
          color: #1C1C1C !important;
        }

        h1, h2 {
          font-family: 'DM Serif Display', Georgia, serif !important;
          font-weight: 400 !important;
          color: #1A3D22 !important;
          letter-spacing: -0.02em;
        }

        h3, h4, h5 {
          font-family: 'DM Sans', system-ui, sans-serif !important;
          font-weight: 600 !important;
          color: #1A3D22 !important;
        }

        /* Fond */
        .stApp {
          background-color: #F5F2EC !important;
        }

        .stApp > header {
          background-color: transparent !important;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
          background: #1A3D22 !important;
          border-right: none !important;
        }

        [data-testid="stSidebar"] *,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] div {
          color: #D4F0D8 !important;
        }

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
          color: #D4F0D8 !important;
        }

        [data-testid="stSidebar"] a {
          color: #7FC686 !important;
          text-decoration: none;
        }

        [data-testid="stSidebar"] hr {
          border-color: rgba(212, 240, 216, 0.2) !important;
        }

        [data-testid="stSidebarNavItems"] {
          padding-top: 0.5rem;
        }

        [data-testid="stSidebarNavLink"] {
          color: #D4F0D8 !important;
          border-radius: 6px !important;
          transition: background 0.15s ease;
        }

        [data-testid="stSidebarNavLink"]:hover {
          background: rgba(212, 240, 216, 0.12) !important;
        }

        [data-testid="stSidebarNavLink"][aria-current="page"] {
          background: rgba(127, 198, 134, 0.2) !important;
          font-weight: 600 !important;
        }

        /* Sidebar buttons */
        [data-testid="stSidebar"] .stButton > button[kind="primary"] {
          background: #7FC686 !important;
          color: #1A3D22 !important;
          border: none !important;
        }

        [data-testid="stSidebar"] .stButton > button[kind="secondary"],
        [data-testid="stSidebar"] .stButton > button:not([kind]) {
          background: transparent !important;
          color: #D4F0D8 !important;
          border: 1.5px solid rgba(212, 240, 216, 0.4) !important;
        }

        /* Boutons zone principale */
        .stButton > button {
          font-family: 'DM Sans', sans-serif !important;
          font-weight: 500 !important;
          border-radius: 8px !important;
          transition: all 0.15s ease !important;
        }

        .stButton > button[kind="primary"] {
          background: #1A3D22 !important;
          color: #D4F0D8 !important;
          border: none !important;
          padding: 0.5rem 1.25rem !important;
        }

        .stButton > button[kind="primary"]:hover {
          background: #2A5C34 !important;
          box-shadow: 0 2px 8px rgba(26, 61, 34, 0.25) !important;
          transform: translateY(-1px);
        }

        .stButton > button[kind="secondary"] {
          background: transparent !important;
          color: #1A3D22 !important;
          border: 1.5px solid #1A3D22 !important;
        }

        .stButton > button[kind="secondary"]:hover {
          background: #D4F0D8 !important;
        }

        /* Page links */
        [data-testid="stPageLink"] a {
          color: #1A3D22 !important;
          font-weight: 500 !important;
        }

        /* Inputs */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div > select,
        .stNumberInput > div > div > input {
          font-family: 'DM Sans', sans-serif !important;
          border: 1.5px solid #E5E0D8 !important;
          border-radius: 8px !important;
          background: #FFFFFF !important;
          color: #1C1C1C !important;
        }

        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
          border-color: #1A3D22 !important;
          box-shadow: 0 0 0 2px rgba(26, 61, 34, 0.12) !important;
        }

        /* Metriques */
        [data-testid="stMetric"] {
          background: white !important;
          border-radius: 12px !important;
          padding: 1rem !important;
          border: 1px solid #E5E0D8 !important;
        }

        [data-testid="stMetric"] label {
          color: #6B7280 !important;
          font-size: 0.78rem !important;
          letter-spacing: 0.04em !important;
          text-transform: uppercase !important;
        }

        [data-testid="stMetricValue"] {
          font-family: 'DM Serif Display', Georgia, serif !important;
          color: #1A3D22 !important;
          font-size: 2rem !important;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
          border-bottom: 2px solid #E5E0D8 !important;
          background: transparent !important;
        }

        .stTabs [data-baseweb="tab"] {
          font-family: 'DM Sans', sans-serif !important;
          font-weight: 500 !important;
          color: #6B7280 !important;
          border-bottom: 2px solid transparent !important;
          margin-bottom: -2px !important;
        }

        .stTabs [aria-selected="true"] {
          color: #1A3D22 !important;
          border-bottom-color: #1A3D22 !important;
        }

        /* File uploader */
        [data-testid="stFileUploader"] {
          border: 2px dashed #E5E0D8 !important;
          border-radius: 12px !important;
          background: white !important;
          transition: border-color 0.15s ease !important;
        }

        [data-testid="stFileUploader"]:hover {
          border-color: #1A3D22 !important;
        }

        [data-testid="stFileUploader"] * {
          color: #1C1C1C !important;
        }

        /* Alertes */
        .stSuccess {
          background: rgba(127, 198, 134, 0.15) !important;
          border-left: 4px solid #7FC686 !important;
          border-radius: 0 8px 8px 0 !important;
        }

        .stWarning {
          background: #FDF3E3 !important;
          border-left: 4px solid #C17B2A !important;
          border-radius: 0 8px 8px 0 !important;
        }

        .stError {
          background: #FDF0F0 !important;
          border-left: 4px solid #B53030 !important;
          border-radius: 0 8px 8px 0 !important;
        }

        /* Expanders */
        .streamlit-expanderHeader {
          color: #1C1C1C !important;
          font-family: 'DM Sans', sans-serif !important;
        }

        /* Progress */
        .stProgress > div > div > div {
          background: #1A3D22 !important;
        }

        /* Separateurs */
        hr {
          border-color: #E5E0D8 !important;
          margin: 1.5rem 0 !important;
        }

        /* Scrollbar */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #F5F2EC; }
        ::-webkit-scrollbar-thumb { background: #E5E0D8; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #2A5C34; }

        /* Masquer menu Streamlit et footer par defaut */
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }

        /* Dataframes */
        [data-testid="stDataFrame"] th {
          background: #1A3D22 !important;
          color: #D4F0D8 !important;
          font-family: 'DM Sans', sans-serif !important;
          font-size: 0.82rem !important;
          letter-spacing: 0.03em !important;
        }

        /* Radio buttons */
        .stRadio label span {
          color: #1C1C1C !important;
        }

        /* Checkboxes */
        .stCheckbox label span {
          color: #1C1C1C !important;
        }

        /* Caption */
        .stCaption, small {
          color: #6B7280 !important;
        }

        /* Markdown text */
        .stMarkdown, .stMarkdown p, .stMarkdown li {
          color: #1C1C1C !important;
        }

        /* Download button */
        .stDownloadButton > button {
          background: #1A3D22 !important;
          color: #D4F0D8 !important;
          border: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def score_color(score: int) -> str:
    """Couleur adaptee au score ESG (0-100)."""
    if score >= 70:
        return COLORS["forest"]
    elif score >= 40:
        return COLORS["amber"]
    return COLORS["alert"]


def score_badge_html(score: int, label: str = "Score global") -> str:
    """HTML d'un badge score (pour st.markdown unsafe_allow_html)."""
    color = score_color(score)
    if score >= 70:
        bg = COLORS["mint"]
    elif score >= 40:
        bg = COLORS["amber_light"]
    else:
        bg = COLORS["alert_light"]

    return (
        f'<div style="display:inline-flex;flex-direction:column;align-items:center;'
        f'background:{bg};border:2px solid {color};border-radius:12px;'
        f'padding:1rem 1.5rem;min-width:120px;">'
        f'<span style="font-family:DM Serif Display,serif;font-size:2.5rem;'
        f'font-weight:400;color:{color};line-height:1;">{score}</span>'
        f'<span style="font-family:DM Sans,sans-serif;font-size:0.72rem;'
        f'color:{color};letter-spacing:0.06em;text-transform:uppercase;'
        f'margin-top:4px;">{label}</span></div>'
    )
