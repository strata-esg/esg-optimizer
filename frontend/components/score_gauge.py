"""
ESG Optimizer MVP - Composant jauge circulaire de score (Plotly).
Affiche un score 0-100 sous forme de gauge colorée.
"""

import plotly.graph_objects as go
import streamlit as st


def _score_color(score: float) -> str:
    """Retourne une couleur selon le niveau du score."""
    if score >= 80:
        return "#1A3D22"   # vert - mature
    elif score >= 60:
        return "#3B82F6"   # bleu - correct
    elif score >= 40:
        return "#F59E0B"   # orange - moyen
    else:
        return "#EF4444"   # rouge - faible


def render_gauge(
    score: float,
    title: str = "Score",
    height: int = 220,
    show_label: bool = True,
) -> None:
    """
    Affiche une jauge circulaire Plotly pour un score 0-100.

    Args:
        score: Valeur numérique 0-100.
        title: Libellé affiché sous la jauge.
        height: Hauteur du graphique en pixels.
        show_label: Afficher le libellé sous la valeur.
    """
    color = _score_color(score)

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": "/100", "font": {"size": 28, "color": color}},
            title={"text": title, "font": {"size": 14}} if show_label else None,
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#E5E7EB"},
                "bar": {"color": color, "thickness": 0.75},
                "bgcolor": "#F3F4F6",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 40], "color": "#FEE2E2"},
                    {"range": [40, 60], "color": "#FEF3C7"},
                    {"range": [60, 80], "color": "#DBEAFE"},
                    {"range": [80, 100], "color": "#D4F0D8"},
                ],
                "threshold": {
                    "line": {"color": color, "width": 3},
                    "thickness": 0.8,
                    "value": score,
                },
            },
        )
    )

    fig.update_layout(
        height=height,
        margin={"t": 30, "b": 10, "l": 30, "r": 30},
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, sans-serif"},
    )

    st.plotly_chart(fig, use_container_width=True, key=f"gauge_{title}_{score}")


def render_score_row(
    score_env: float,
    score_social: float,
    score_gov: float,
    score_global: float,
) -> None:
    """
    Affiche le score global en grand + 3 sous-scores E/S/G côte à côte.
    """
    # Score global - centré, plus grand
    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        render_gauge(score_global, title="Score Global", height=280)

    # Sous-scores E / S / G
    col_e, col_s, col_g = st.columns(3)
    with col_e:
        render_gauge(score_env, title="Environnement", height=200)
    with col_s:
        render_gauge(score_social, title="Social", height=200)
    with col_g:
        render_gauge(score_gov, title="Gouvernance", height=200)
