"""
ESG Optimizer MVP — Page Dashboard.
Historique des analyses, stats agrégées, graphiques de tendance.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

# --- IMPORT & INJECTION SEO ---
from frontend.components.seo import seo_for
seo_for("dashboard")

from frontend.utils.api_client import APIError, get_history, get_stats, get_companies
from frontend.utils.session import get_token, get_user, require_auth, save_last_analysis_id

if not require_auth():
    st.stop()

token = get_token()
try:
    from frontend.utils.api_client import get_me
    from frontend.utils.session import save_user
    _user_info = get_me(token)
    save_user(_user_info)
except Exception:
    _user_info = get_user()
_user_plan = _user_info.get("plan", "discovery") if _user_info else "discovery"

# Bandeau upgrade (plan gratuit)
if _user_plan in ("discovery", "free"):
    st.markdown(
        """<div style="background: linear-gradient(135deg, #EFF6FF 0%, #F0FDF4 100%);
            border: 1px solid #1A3D22; border-radius: 12px; padding: 16px; text-align: center;
            margin-bottom: 16px;">
            <span style="font-weight: 600; color: #111827;">
                Plan Découverte — </span>
            <span style="color: #6B7280;">
                Passez au Pro pour des analyses illimitées, l'export Excel et le benchmark sectoriel.
            </span>
        </div>""",
        unsafe_allow_html=True,
    )
    col_d1, col_d2, col_d3 = st.columns([2, 1, 2])
    with col_d2:
        if st.button("Voir les tarifs", key="dash_upgrade", use_container_width=True, type="primary"):
            st.switch_page("pages/6_Tarifs.py")

# Header
st.markdown(
    """<div style="padding: 10px 0 20px 0;">
        <h2>Dashboard ESG</h2>
        <p style="color: #6B7280;">Vue d'ensemble de vos analyses et tendances ESG.</p>
    </div>""",
    unsafe_allow_html=True,
)

# 1. STATS AGRÉGÉES (header KPIs)
try:
    stats = get_stats(token)
except APIError as e:
    st.error(f"Erreur chargement stats : {e.detail}")
    stats = {}
except Exception:
    stats = {}

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total analyses", stats.get("total_analyses", 0))
with col2:
    avg = stats.get("avg_score_global")
    st.metric("Score moyen global", f"{avg:.1f}/100" if avg else "—")
with col3:
    csrd_pct = stats.get("csrd_ready_pct")
    st.metric("% CSRD Ready", f"{csrd_pct:.0f}%" if csrd_pct is not None else "—")
with col4:
    avg_env = stats.get("avg_score_env")
    st.metric("Score moyen E", f"{avg_env:.1f}" if avg_env else "—")

st.markdown("---")

# 2. HISTORIQUE DES ANALYSES (tableau paginé)
st.subheader("Historique des analyses")

# Pagination
page = st.number_input("Page", min_value=1, value=1, step=1, label_visibility="collapsed")

try:
    history = get_history(token, page=page, per_page=20)
except APIError as e:
    st.error(f"Erreur : {e.detail}")
    history = {"analyses": [], "total": 0, "page": 1, "per_page": 20}
except Exception:
    history = {"analyses": [], "total": 0, "page": 1, "per_page": 20}

analyses_list = history.get("analyses", [])

if analyses_list:
    df = pd.DataFrame(analyses_list)

    # Formatage des colonnes
    column_map = {
        "id": "ID",
        "company_name": "Entreprise",
        "report_year": "Année",
        "score_global": "Score Global",
        "csrd_ready": "CSRD Ready",
        "status": "Statut",
        "created_at": "Date",
    }
    existing = [c for c in column_map if c in df.columns]
    df_display = df[existing].rename(columns=column_map)

    # Formatage visuel du statut
    if "Statut" in df_display.columns:
        df_display["Statut"] = df_display["Statut"].map(
            {"success": "Terminé", "processing": "En cours", "pending": "En attente", "failed": "Échec"}
        ).fillna("?")

    if "CSRD Ready" in df_display.columns:
        df_display["CSRD Ready"] = df_display["CSRD Ready"].map({True: "Oui", False: "Non", None: "—"})

    if "Score Global" in df_display.columns:
        df_display["Score Global"] = df_display["Score Global"].apply(
            lambda x: f"{x:.0f}/100" if pd.notnull(x) else "—"
        )

    # Affichage
    event = st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
    )

    # Clic sur une ligne → aller aux résultats
    if event and event.selection and event.selection.rows:
        selected_idx = event.selection.rows[0]
        selected_id = analyses_list[selected_idx]["id"]
        save_last_analysis_id(selected_id)
        st.page_link("pages/3_Resultats.py", label=f"Voir l'analyse #{selected_id}")

    total = history.get("total", 0)
    per_page = history.get("per_page", 20)
    st.caption(f"Page {page} — {total} analyse(s) au total")

else:
    st.info("Aucune analyse pour le moment. Lancez votre première analyse depuis la page Upload !")
    st.page_link("pages/2_Upload.py", label="Lancer une analyse")

# 3. GRAPHIQUES (si données suffisantes)
if analyses_list and len(analyses_list) >= 2:
    st.markdown("---")

    # Charger toutes les analyses pour les graphiques
    try:
        all_history = get_history(token, page=1, per_page=100)
        all_analyses = all_history.get("analyses", [])
    except Exception:
        all_analyses = analyses_list

    # Filtrer les analyses terminées avec un score
    completed = [a for a in all_analyses if a.get("score_global") is not None]

    if completed:
        chart_df = pd.DataFrame(completed)
        chart_df["created_at"] = pd.to_datetime(chart_df["created_at"])

        col_bar, col_line = st.columns(2)

        # Graphique barres : scores par entreprise
        with col_bar:
            st.subheader("Scores par entreprise")
            latest_per_company = (
                chart_df.sort_values("created_at", ascending=False)
                .groupby("company_name")
                .first()
                .reset_index()
            )
            if not latest_per_company.empty and "score_global" in latest_per_company.columns:
                fig_bar = px.bar(
                    latest_per_company,
                    x="company_name",
                    y="score_global",
                    color="score_global",
                    color_continuous_scale=["#EF4444", "#F59E0B", "#3B82F6", "#1A3D22"],
                    range_color=[0, 100],
                    labels={"company_name": "Entreprise", "score_global": "Score Global"},
                )
                fig_bar.update_layout(
                    height=350,
                    showlegend=False,
                    margin={"t": 20, "b": 40},
                )
                st.plotly_chart(fig_bar, use_container_width=True)

        # Courbe temporelle : évolution des scores
        with col_line:
            st.subheader("Évolution temporelle")
            if len(chart_df) >= 2:
                fig_line = go.Figure()
                fig_line.add_trace(go.Scatter(
                    x=chart_df["created_at"], y=chart_df["score_global"],
                    mode="lines+markers", name="Global",
                    line={"color": "#6366F1", "width": 3},
                ))
                fig_line.update_layout(
                    height=350,
                    yaxis={"range": [0, 100], "title": "Score"},
                    xaxis={"title": "Date"},
                    margin={"t": 20, "b": 40},
                )
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.caption("Au moins 2 analyses nécessaires pour le graphique temporel.")
