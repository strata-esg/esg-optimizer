"""
Sidebar ESG Optimizer : logo, navigation, infos utilisateur.
"""

import streamlit as st

from frontend.utils.session import get_user, is_logged_in, logout, clear_jwt_cookie


def render_sidebar() -> None:
    with st.sidebar:
        # Logo
        st.markdown(
            """<div style="padding: 16px 8px 20px 8px;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"
                         fill="none" width="38" height="38">
                        <path d="M 6,24 A 14,14 0 1,1 34,24"
                            stroke="rgba(212,240,216,0.3)" stroke-width="3.5"
                            stroke-linecap="round" fill="none"/>
                        <path d="M 6,24 A 14,14 0 0,1 28,9"
                            stroke="#7FC686" stroke-width="3.5"
                            stroke-linecap="round" fill="none"/>
                        <circle cx="20" cy="22" r="2.5" fill="#D4F0D8"/>
                        <line x1="20" y1="22" x2="30" y2="10"
                            stroke="#D4F0D8" stroke-width="2" stroke-linecap="round"/>
                        <circle cx="30" cy="10" r="2" fill="#7FC686"/>
                    </svg>
                    <div>
                        <div style="font-family:'DM Serif Display',Georgia,serif;
                                    font-size:16px; font-weight:400;
                                    color:#D4F0D8; letter-spacing:-0.02em;">
                            ESG Optimizer
                        </div>
                        <div style="font-family:'DM Sans',sans-serif;
                                    font-size:10px; color:#7FC686;
                                    letter-spacing:0.08em; text-transform:uppercase;
                                    margin-top:1px;">
                            Conformité CSRD
                        </div>
                    </div>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )
        st.divider()

        # Navigation
        st.page_link("pages/0_Accueil.py", label="Accueil")
        if is_logged_in():
            st.page_link("pages/2_Upload.py", label="Upload")
            st.page_link("pages/3_Resultats.py", label="Résultats")
            st.page_link("pages/4_Dashboard.py", label="Dashboard")
            st.page_link("pages/5_Parametres.py", label="Paramètres")
        st.page_link("pages/6_Tarifs.py", label="Tarifs")
        st.page_link("pages/7_Mentions.py", label="Mentions")

        st.divider()

        # Infos utilisateur
        if is_logged_in():
            user = get_user()
            if user:
                plan = user.get("plan", "discovery")
                plan_badges = {
                    "discovery":  ("Découverte",  "rgba(212,240,216,0.2)", "#D4F0D8"),
                    "free":       ("Découverte",  "rgba(212,240,216,0.2)", "#D4F0D8"),
                    "essential":  ("Essentiel",   "rgba(127,198,134,0.3)", "#7FC686"),
                    "pro":        ("Pro",          "rgba(127,198,134,0.4)", "#7FC686"),
                    "enterprise": ("Enterprise",  "rgba(127,198,134,0.4)", "#7FC686"),
                }
                label, bg, color = plan_badges.get(plan, plan_badges["discovery"])
                st.markdown(
                    f"""<div style="padding: 4px 0;">
                        <div style="font-weight:500; font-size:13px; color:#D4F0D8;">
                            {user.get('email', '')}
                        </div>
                        <div style="margin-top:6px;">
                            <span style="background:{bg}; color:{color}; padding:2px 8px;
                                border-radius:10px; font-size:11px; font-weight:600;">
                                {label}
                            </span>
                            <span style="font-size:11px; color:rgba(212,240,216,0.5); margin-left:8px;">
                                {user.get('analyses_this_month', 0)} analyse(s) ce mois
                            </span>
                        </div>
                    </div>""",
                    unsafe_allow_html=True,
                )

                st.divider()

                if plan in ("discovery", "free"):
                    if st.button("Passer au plan Pro", use_container_width=True, type="primary", key="sidebar_upgrade"):
                        st.switch_page("pages/6_Tarifs.py")

            if st.button("Se déconnecter", use_container_width=True, type="secondary"):
                clear_jwt_cookie()
                logout()
                st.session_state.pop("_cookie_checked", None)
                st.rerun()
        else:
            st.caption("Non connecté")
            if st.button("Se connecter", use_container_width=True, type="primary", key="sidebar_login"):
                st.switch_page("pages/1_Login.py")

        # Version
        st.markdown(
            '<div style="position:fixed; bottom:16px; font-size:10px; '
            'color:rgba(212,240,216,0.35); letter-spacing:0.04em;">'
            'ESG Optimizer v1.0</div>',
            unsafe_allow_html=True,
        )
