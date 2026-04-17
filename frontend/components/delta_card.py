"""
ESG Optimizer MVP — Composant carte delta avec indicateur de tendance.
Affiche le delta entre deux analyses (flèches, couleurs, valeur).
"""

import streamlit as st


def _trend_icon(delta: float) -> tuple[str, str, str]:
    """
    Retourne (icône, couleur, label) selon le delta.
    """
    if delta > 5:
        return "&#9650;", "#10B981", "Forte amélioration"
    elif delta > 0:
        return "&#9650;", "#3B82F6", "Amélioration"
    elif delta == 0:
        return "&#9654;", "#6B7280", "Stable"
    elif delta > -5:
        return "&#9660;", "#F59E0B", "Légère dégradation"
    else:
        return "&#9660;", "#EF4444", "Dégradation"


def render_delta_card(
    label: str,
    delta: float | None,
    current_score: float | None = None,
) -> None:
    """
    Affiche une carte delta avec flèche de tendance.

    Args:
        label: Nom du pilier (ex: "Environnement").
        delta: Écart avec l'analyse précédente. None si pas de delta.
        current_score: Score actuel (optionnel, affiché si fourni).
    """
    if delta is None:
        st.markdown(
            f"""<div style="
                background: #F9FAFB; border: 1px solid #E5E7EB;
                border-radius: 10px; padding: 16px; text-align: center;">
                <div style="font-weight: 600; color: #6B7280; font-size: 13px;">{label}</div>
                <div style="color: #9CA3AF; font-size: 12px; margin-top: 8px;">Pas de comparaison</div>
            </div>""",
            unsafe_allow_html=True,
        )
        return

    icon, color, trend_label = _trend_icon(delta)
    score_html = (
        f'<div style="font-size: 11px; color: #9CA3AF; margin-top: 4px;">Score actuel : {current_score:.0f}/100</div>'
        if current_score is not None
        else ""
    )

    st.markdown(
        f"""<div style="
            background: white; border: 2px solid {color}22;
            border-radius: 12px; padding: 16px; text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);">
            <div style="font-weight: 600; color: #374151; font-size: 13px;">{label}</div>
            <div style="font-size: 32px; color: {color}; margin: 8px 0; font-weight: 700;">
                {icon} {delta:+.1f}
            </div>
            <div style="font-size: 12px; color: {color}; font-weight: 500;">{trend_label}</div>
            {score_html}
        </div>""",
        unsafe_allow_html=True,
    )


def render_delta_row(analysis: dict) -> None:
    """
    Affiche une rangée de 4 cartes delta (E / S / G / Global).
    Ne s'affiche que si au moins un delta est disponible.

    Args:
        analysis: dict contenant delta_env, delta_social, delta_gov, delta_global
                  et score_env, score_social, score_gov, score_global.
    """
    has_delta = any(
        analysis.get(k) is not None
        for k in ("delta_env", "delta_social", "delta_gov", "delta_global")
    )

    if not has_delta:
        return

    st.subheader("Évolution vs analyse précédente")

    col_e, col_s, col_g, col_gl = st.columns(4)
    with col_e:
        render_delta_card("Environnement", analysis.get("delta_env"), analysis.get("score_env"))
    with col_s:
        render_delta_card("Social", analysis.get("delta_social"), analysis.get("score_social"))
    with col_g:
        render_delta_card("Gouvernance", analysis.get("delta_gov"), analysis.get("score_gov"))
    with col_gl:
        render_delta_card("Global", analysis.get("delta_global"), analysis.get("score_global"))

    # Synthèse narrative si disponible
    narrative = analysis.get("delta_narrative")
    if narrative:
        st.markdown("---")
        st.markdown("**Synthèse d'évolution**")
        st.info(narrative)
