"""
ESG Optimizer MVP — Composant sidebar (branding + navigation + user info).
"""

import streamlit as st

from frontend.utils.session import get_user, is_logged_in, logout


def render_sidebar() -> None:
    """
    Affiche la sidebar avec :
    - Logo / branding ESG Optimizer
    - Infos utilisateur connecté
    - Bouton déconnexion
    """
    with st.sidebar:
        # ── Branding ────────────────────────────────────
        st.markdown(
            """<div style="text-align: center; padding: 10px 0 20px 0;">
                <div style="font-size: 28px; font-weight: 800; color: #10B981;">
                    ESG Optimizer
                </div>
                <div style="font-size: 12px; color: #6B7280; margin-top: 4px;">
                    Reporting ESG intelligent
                </div>
            </div>""",
            unsafe_allow_html=True,
        )
        st.divider()

        # ── Infos utilisateur ───────────────────────────
        if is_logged_in():
            user = get_user()
            if user:
                plan_badge = (
                    '<span style="background: #10B981; color: white; padding: 2px 8px; '
                    'border-radius: 10px; font-size: 11px; font-weight: 600;">PRO</span>'
                    if user.get("plan") == "pro"
                    else '<span style="background: #E5E7EB; color: #374151; padding: 2px 8px; '
                    'border-radius: 10px; font-size: 11px; font-weight: 600;">FREE</span>'
                )
                st.markdown(
                    f"""<div style="padding: 8px 0;">
                        <div style="font-weight: 600; font-size: 14px; color: #111827;">
                            {user.get('email', '')}
                        </div>
                        <div style="margin-top: 6px;">
                            {plan_badge}
                            <span style="font-size: 11px; color: #9CA3AF; margin-left: 8px;">
                                {user.get('analyses_this_month', 0)} analyse(s) ce mois
                            </span>
                        </div>
                    </div>""",
                    unsafe_allow_html=True,
                )

                st.divider()

            # ── Bouton déconnexion ──────────────────────
            if st.button("Se déconnecter", use_container_width=True, type="secondary"):
                logout()
                st.rerun()
        else:
            st.caption("Non connecté")

        # ── Footer ──────────────────────────────────────
        st.markdown(
            """<div style="position: fixed; bottom: 20px; font-size: 11px; color: #9CA3AF;">
                ESG Optimizer AI v0.1.0
            </div>""",
            unsafe_allow_html=True,
        )
