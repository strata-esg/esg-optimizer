"""
ESG Optimizer MVP - Dashboard premium.
Stats agrégées, historique enrichi, Delta Report N/N-1.
"""

import json
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from frontend.components.seo import seo_for
seo_for("dashboard")

from frontend.utils.styles import inject_global_styles, COLORS
inject_global_styles()

from frontend.utils.api_client import (
    APIError,
    get_history,
    get_stats,
    get_companies,
    get_analysis,
    recompute_delta,
)
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
_user_name = (_user_info.get("full_name") or _user_info.get("company_name") or "") if _user_info else ""
_is_paid = _user_plan not in ("discovery", "free")


# Styles additionnels dashboard
st.markdown("""
<style>
/* Hero header gradient */
.dash-hero {
    background: linear-gradient(135deg, #1B3D20 0%, #2F6830 60%, #3A7D3C 100%);
    border-radius: 16px;
    padding: 32px 36px;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
}
.dash-hero::after {
    content: "";
    position: absolute;
    right: -30px; top: -30px;
    width: 200px; height: 200px;
    border-radius: 50%;
    background: rgba(127,198,134,0.12);
    pointer-events: none;
}
.dash-hero h1 {
    font-family: 'DM Serif Display', serif !important;
    font-size: 2rem !important;
    color: #FFFFFF !important;
    margin: 0 0 6px 0;
    letter-spacing: -0.02em;
}
.dash-hero p {
    color: #96D9A2 !important;
    font-size: 0.95rem !important;
    margin: 0;
}
.dash-hero .plan-badge {
    display: inline-block;
    background: rgba(127,198,134,0.25);
    border: 1px solid rgba(127,198,134,0.5);
    color: #96D9A2 !important;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 20px;
    margin-bottom: 10px;
}

/* KPI cards */
.kpi-card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 14px;
    padding: 20px 18px;
    text-align: center;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    transition: box-shadow 0.2s ease;
}
.kpi-card:hover { box-shadow: 0 4px 12px rgba(27,61,32,0.1); }
.kpi-value {
    font-family: 'DM Serif Display', Georgia, serif;
    font-size: 2.4rem;
    color: #1B3D20;
    line-height: 1;
    margin: 4px 0;
}
.kpi-label {
    font-size: 0.72rem;
    font-weight: 600;
    color: #6B7280;
    text-transform: uppercase;
    letter-spacing: 0.07em;
}
.kpi-sub {
    font-size: 0.78rem;
    color: #9CA3AF;
    margin-top: 4px;
}

/* Section title */
.section-title {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.7rem !important;
    font-weight: 700 !important;
    color: #6B7280 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    margin: 0 0 12px 2px;
}

/* Upgrade banner */
.upgrade-bar {
    background: linear-gradient(135deg, #FEF3C7 0%, #FDF6E3 100%);
    border: 1px solid #F59E0B;
    border-radius: 12px;
    padding: 14px 20px;
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 20px;
}

/* Delta section */
.delta-hero {
    background: linear-gradient(135deg, #EFF6FF 0%, #F0FDF4 100%);
    border: 1.5px solid #BFDBFE;
    border-radius: 14px;
    padding: 22px 24px;
    margin-bottom: 20px;
}
.delta-no-data {
    background: #FFFBEB;
    border: 1.5px solid #FDE68A;
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
}
.delta-card {
    background: white;
    border-radius: 12px;
    padding: 18px;
    text-align: center;
    border: 1.5px solid;
}
.delta-pill-up {
    background: #D1FAE5;
    color: #065F46;
    font-size: 0.7rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 20px;
    display: inline-block;
}
.delta-pill-down {
    background: #FEE2E2;
    color: #991B1B;
    font-size: 0.7rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 20px;
    display: inline-block;
}
.delta-pill-neutral {
    background: #F3F4F6;
    color: #6B7280;
    font-size: 0.7rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 20px;
    display: inline-block;
}

/* Table rows */
.analysis-row {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 16px;
    transition: box-shadow 0.15s ease;
    cursor: pointer;
}
.analysis-row:hover { box-shadow: 0 2px 8px rgba(27,61,32,0.1); }
</style>
""", unsafe_allow_html=True)


# Chargement des données
@st.cache_data(ttl=30)
def _load_stats(tok):
    try:
        return get_stats(tok)
    except Exception:
        return {}

@st.cache_data(ttl=30)
def _load_history(tok, page, per_page):
    try:
        return get_history(tok, page=page, per_page=100)
    except Exception:
        return {"analyses": [], "total": 0}

@st.cache_data(ttl=60)
def _load_companies(tok):
    try:
        return get_companies(tok)
    except Exception:
        return []


stats = _load_stats(token)
all_history = _load_history(token, 1, 100)
all_analyses = all_history.get("analyses", [])
companies = _load_companies(token)


# HERO HEADER
plan_labels = {
    "discovery": "Plan Découverte",
    "free": "Plan Gratuit",
    "essential": "Plan Essentiel",
    "pro": "Plan Pro",
    "enterprise": "Plan Entreprise",
}
plan_label = plan_labels.get(_user_plan, _user_plan.capitalize())
greet = f"Bonjour{', ' + _user_name.split()[0] if _user_name else ''} 👋" if _user_name else "Dashboard ESG"

st.markdown(f"""
<div class="dash-hero">
    <div class="plan-badge">{plan_label}</div>
    <h1>{greet}</h1>
    <p>Vue d'ensemble de vos analyses CSRD/ESRS et tendances ESG.</p>
</div>
""", unsafe_allow_html=True)


# BANDEAU UPGRADE (plan gratuit)
if not _is_paid:
    col_up1, col_up2 = st.columns([5, 1])
    with col_up1:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#FEF3C7 0%,#FDF6E3 100%);
            border:1px solid #F59E0B;border-radius:12px;padding:14px 20px;">
            <span style="font-weight:700;color:#92400E;">Plan Découverte</span>
            <span style="color:#78350F;"> — Passez au Pro pour des analyses illimitées,
            le Delta Report, l'export PDF complet et le benchmark sectoriel.</span>
        </div>
        """, unsafe_allow_html=True)
    with col_up2:
        if st.button("Voir les tarifs", key="dash_upgrade", use_container_width=True, type="primary"):
            st.switch_page("pages/6_Tarifs.py")
    st.markdown("<br>", unsafe_allow_html=True)


# KPI CARDS
st.markdown('<p class="section-title">Indicateurs globaux</p>', unsafe_allow_html=True)

total_analyses = stats.get("total_analyses", 0)
avg_global = stats.get("avg_score_global")
avg_env = stats.get("avg_score_env")
avg_social = stats.get("avg_score_social")
avg_gov = stats.get("avg_score_gov")
csrd_pct = stats.get("csrd_ready_pct")

def _score_color_hex(score):
    if score is None:
        return "#9CA3AF"
    if score >= 70:
        return "#1B3D20"
    if score >= 40:
        return "#D97706"
    return "#DC2626"

def _kpi_card(value, label, sub="", color="#1B3D20"):
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value" style="color:{color};">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>"""

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.markdown(_kpi_card(total_analyses, "Analyses", "au total"), unsafe_allow_html=True)
with c2:
    v = f"{avg_global:.0f}" if avg_global else "-"
    st.markdown(_kpi_card(v, "Score global moy.", "/100", _score_color_hex(avg_global)), unsafe_allow_html=True)
with c3:
    v = f"{csrd_pct:.0f}%" if csrd_pct is not None else "-"
    col = "#1B3D20" if csrd_pct and csrd_pct >= 50 else "#D97706" if csrd_pct else "#9CA3AF"
    st.markdown(_kpi_card(v, "CSRD Ready", "des analyses", col), unsafe_allow_html=True)
with c4:
    v = f"{avg_env:.0f}" if avg_env else "-"
    st.markdown(_kpi_card(v, "Score Env. moy.", "/100", _score_color_hex(avg_env)), unsafe_allow_html=True)
with c5:
    v = f"{avg_gov:.0f}" if avg_gov else "-"
    st.markdown(_kpi_card(v, "Score Gov. moy.", "/100", _score_color_hex(avg_gov)), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# GRAPHIQUES (si données suffisantes)
completed = [a for a in all_analyses if a.get("score_global") is not None]

if len(completed) >= 2:
    chart_df = pd.DataFrame(completed)
    chart_df["created_at"] = pd.to_datetime(chart_df["created_at"])
    chart_df = chart_df.sort_values("created_at")

    col_bar, col_radar = st.columns([1, 1])

    with col_bar:
        st.markdown('<p class="section-title">Score global par entreprise</p>', unsafe_allow_html=True)
        latest_per_company = (
            chart_df.sort_values("created_at", ascending=False)
            .groupby("company_name")
            .first()
            .reset_index()
            .sort_values("score_global", ascending=True)
        )
        fig_bar = go.Figure(go.Bar(
            x=latest_per_company["score_global"],
            y=latest_per_company["company_name"],
            orientation="h",
            marker=dict(
                color=latest_per_company["score_global"],
                colorscale=[[0, "#DC2626"], [0.4, "#F59E0B"], [0.7, "#4DB862"], [1, "#1B3D20"]],
                cmin=0, cmax=100,
            ),
            text=[f"{v:.0f}/100" for v in latest_per_company["score_global"]],
            textposition="outside",
        ))
        fig_bar.update_layout(
            height=max(200, len(latest_per_company) * 52),
            margin=dict(t=10, b=10, l=10, r=60),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(range=[0, 110], showgrid=True, gridcolor="#F3F4F6", zeroline=False, tickfont=dict(color="#6B7280")),
            yaxis=dict(showgrid=False, tickfont=dict(color="#374151", size=12)),
            font=dict(family="DM Sans"),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_radar:
        st.markdown('<p class="section-title">Évolution temporelle</p>', unsafe_allow_html=True)
        fig_line = go.Figure()
        for pillar, col_name, color in [
            ("Global", "score_global", "#1B3D20"),
            ("Env.", "score_env", "#4DB862"),
            ("Social", "score_social", "#3B82F6"),
            ("Gov.", "score_gov", "#D97706"),
        ]:
            sub = chart_df[chart_df[col_name].notna()] if col_name in chart_df.columns else pd.DataFrame()
            if not sub.empty:
                fig_line.add_trace(go.Scatter(
                    x=sub["created_at"],
                    y=sub[col_name],
                    mode="lines+markers",
                    name=pillar,
                    line=dict(color=color, width=2.5),
                    marker=dict(size=6, color=color),
                ))
        fig_line.update_layout(
            height=max(200, len(latest_per_company) * 52) if "latest_per_company" in dir() else 300,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(range=[0, 105], title="Score", gridcolor="#F3F4F6", tickfont=dict(color="#6B7280")),
            xaxis=dict(gridcolor="#F3F4F6", tickfont=dict(color="#6B7280")),
            legend=dict(orientation="h", y=-0.18, x=0),
            font=dict(family="DM Sans"),
            margin=dict(t=10, b=40, l=10, r=10),
        )
        st.plotly_chart(fig_line, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)


# DELTA REPORT N/N-1
st.markdown('<p class="section-title">Delta Report N/N-1</p>', unsafe_allow_html=True)

analyses_by_company: dict[str, list[dict]] = {}
for a in all_analyses:
    cname = a.get("company_name", "?")
    analyses_by_company.setdefault(cname, []).append(a)

companies_with_multiple = [c for c, lst in analyses_by_company.items() if len(lst) >= 2]
companies_with_single = [c for c, lst in analyses_by_company.items() if len(lst) == 1]

if not all_analyses:
    st.markdown("""
    <div class="delta-no-data">
        <div style="font-size:2rem;margin-bottom:8px;">📊</div>
        <div style="font-weight:600;color:#374151;margin-bottom:4px;">Aucune analyse disponible</div>
        <div style="color:#6B7280;font-size:0.88rem;">
            Lancez votre première analyse depuis la page Upload pour débloquer le Delta Report.
        </div>
    </div>
    """, unsafe_allow_html=True)
elif not companies_with_multiple:
    # Toutes les entreprises n'ont qu'une seule analyse
    st.markdown(f"""
    <div class="delta-no-data">
        <div style="font-size:2rem;margin-bottom:8px;">🔍</div>
        <div style="font-weight:700;color:#92400E;margin-bottom:6px;">
            Analyse unique détectée
        </div>
        <div style="color:#78350F;font-size:0.9rem;margin-bottom:8px;">
            Le Delta Report compare deux analyses successives de la même entreprise (N vs N-1).
            Importez un second rapport pour
            <b>{", ".join(companies_with_single)}</b> pour débloquer cette fonctionnalité.
        </div>
        <div style="font-size:0.8rem;color:#9CA3AF;">
            Astuce : analysez le rapport de l'année précédente pour visualiser votre progression ESG.
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    # Sélecteur d'entreprise
    col_sel1, col_sel2 = st.columns([2, 3])
    with col_sel1:
        selected_company = st.selectbox(
            "Entreprise",
            options=companies_with_multiple,
            key="delta_company_select",
        )

    company_analyses = sorted(
        analyses_by_company.get(selected_company, []),
        key=lambda a: (a.get("report_year") or 0, a.get("created_at") or ""),
        reverse=True,
    )
    success_analyses = [a for a in company_analyses if a.get("status") == "success"]

    with col_sel2:
        if companies_with_single:
            st.markdown(
                f'<div style="background:#FFFBEB;border:1px solid #FDE68A;border-radius:8px;'
                f'padding:10px 14px;font-size:0.82rem;color:#78350F;margin-top:24px;">'
                f'<b>⚠ Analyse unique</b> pour : {", ".join(companies_with_single)}. '
                f'Un second rapport est nécessaire pour activer le Delta.</div>',
                unsafe_allow_html=True,
            )

    if len(success_analyses) < 2:
        st.markdown("""
        <div class="delta-no-data">
            <div style="font-weight:600;color:#92400E;margin-bottom:4px;">
                Une seule analyse terminée pour cette entreprise
            </div>
            <div style="color:#78350F;font-size:0.88rem;">
                Importez un second rapport ESG pour générer la comparaison N vs N-1.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        analysis_n = success_analyses[0]   # la plus récente
        analysis_n1 = success_analyses[1]  # la précédente

        year_n = analysis_n.get("report_year") or "N"
        year_n1 = analysis_n1.get("report_year") or "N-1"

        # Header Delta
        st.markdown(f"""
        <div class="delta-hero">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:4px;">
                <span style="font-size:1.4rem;">📈</span>
                <span style="font-weight:700;color:#1E40AF;font-size:1rem;">
                    Comparaison {year_n1} → {year_n}
                </span>
                <span style="background:#DBEAFE;color:#1E40AF;font-size:0.7rem;font-weight:700;
                    padding:2px 8px;border-radius:20px;letter-spacing:0.05em;">
                    {selected_company}
                </span>
            </div>
            <p style="color:#374151;font-size:0.85rem;margin:0;">
                Rapport N : <b>{analysis_n.get("source_filename","?")}</b> &nbsp;|&nbsp;
                Rapport N-1 : <b>{analysis_n1.get("source_filename","?")}</b>
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Vérifier si un delta est déjà calculé pour l'analyse N
        has_delta = any(
            analysis_n.get(k) is not None
            for k in ("delta_env", "delta_social", "delta_gov", "delta_global")
        )

        # Bouton Calculer Delta
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
        with col_btn1:
            calculate_delta = st.button(
                "Calculer le Delta",
                key="btn_calc_delta",
                type="primary",
                use_container_width=True,
                disabled=not _is_paid,
            )
        with col_btn2:
            if has_delta:
                st.markdown(
                    '<div style="padding:8px 0;font-size:0.82rem;color:#059669;font-weight:600;">'
                    '&#10003; Delta disponible</div>',
                    unsafe_allow_html=True,
                )

        if not _is_paid:
            st.markdown(
                '<div style="font-size:0.78rem;color:#9CA3AF;margin-top:-8px;">'
                'Le Delta Report est disponible à partir du plan Essentiel.</div>',
                unsafe_allow_html=True,
            )

        # Calcul du delta à la demande
        if calculate_delta and _is_paid:
            with st.spinner("Calcul du delta en cours (analyse IA)..."):
                try:
                    recompute_delta(token, analysis_n["id"])
                    # Invalider le cache pour recharger les données
                    _load_history.clear()
                    st.cache_data.clear()
                    # Recharger l'analyse fraîche
                    analysis_n = get_analysis(token, analysis_n["id"])
                    has_delta = True
                    st.success("Delta calculé avec succès !")
                    st.rerun()
                except APIError as e:
                    if e.status_code == 403:
                        st.error("Le Delta Report est réservé aux plans payants.")
                    elif e.status_code == 404:
                        st.warning("Aucune analyse précédente trouvée pour cette entreprise.")
                    else:
                        st.error(f"Erreur : {e.detail}")
                except Exception as exc:
                    st.error(f"Erreur inattendue : {exc}")

        # Afficher les cartes delta si disponibles
        if has_delta:
            st.markdown("<br>", unsafe_allow_html=True)

            def _delta_card_html(label, delta_val, score_current, score_prev):
                if delta_val is None:
                    return f"""
                    <div class="delta-card" style="border-color:#E5E7EB;">
                        <div style="font-size:0.72rem;font-weight:700;color:#6B7280;
                            text-transform:uppercase;letter-spacing:0.07em;">{label}</div>
                        <div style="font-size:1.6rem;color:#9CA3AF;margin:10px 0;">-</div>
                        <div class="delta-pill-neutral">Non disponible</div>
                    </div>"""

                if delta_val > 5:
                    arrow, pill_cls, bdr = "&#9650;&#9650;", "delta-pill-up", "#10B981"
                    trend = "Forte amélioration"
                elif delta_val > 0:
                    arrow, pill_cls, bdr = "&#9650;", "delta-pill-up", "#34D399"
                    trend = "Amélioration"
                elif delta_val == 0:
                    arrow, pill_cls, bdr = "&#9654;", "delta-pill-neutral", "#9CA3AF"
                    trend = "Stable"
                elif delta_val > -5:
                    arrow, pill_cls, bdr = "&#9660;", "delta-pill-down", "#FBBF24"
                    trend = "Légère dégradation"
                else:
                    arrow, pill_cls, bdr = "&#9660;&#9660;", "delta-pill-down", "#EF4444"
                    trend = "Dégradation"

                sign = "+" if delta_val > 0 else ""
                prev_html = (
                    f'<div style="font-size:0.76rem;color:#9CA3AF;margin-top:6px;">'
                    f'{score_prev:.0f} → <b style="color:#374151;">{score_current:.0f}</b>/100</div>'
                    if score_current is not None and score_prev is not None else ""
                )

                return f"""
                <div class="delta-card" style="border-color:{bdr}22;">
                    <div style="font-size:0.72rem;font-weight:700;color:#6B7280;
                        text-transform:uppercase;letter-spacing:0.07em;margin-bottom:10px;">{label}</div>
                    <div style="font-family:'DM Serif Display',serif;font-size:2rem;
                        color:{bdr};line-height:1;margin-bottom:6px;">
                        {arrow} {sign}{delta_val:.1f}
                    </div>
                    <div class="{pill_cls}">{trend}</div>
                    {prev_html}
                </div>"""

            # Scores de N-1 (approx depuis le delta)
            s_env_n1 = (
                (analysis_n.get("score_env") or 0) - (analysis_n.get("delta_env") or 0)
                if analysis_n.get("score_env") is not None else None
            )
            s_soc_n1 = (
                (analysis_n.get("score_social") or 0) - (analysis_n.get("delta_social") or 0)
                if analysis_n.get("score_social") is not None else None
            )
            s_gov_n1 = (
                (analysis_n.get("score_gov") or 0) - (analysis_n.get("delta_gov") or 0)
                if analysis_n.get("score_gov") is not None else None
            )
            s_gl_n1 = (
                (analysis_n.get("score_global") or 0) - (analysis_n.get("delta_global") or 0)
                if analysis_n.get("score_global") is not None else None
            )

            d1, d2, d3, d4 = st.columns(4)
            with d1:
                st.markdown(
                    _delta_card_html("Environnement", analysis_n.get("delta_env"),
                                     analysis_n.get("score_env"), s_env_n1),
                    unsafe_allow_html=True,
                )
            with d2:
                st.markdown(
                    _delta_card_html("Social", analysis_n.get("delta_social"),
                                     analysis_n.get("score_social"), s_soc_n1),
                    unsafe_allow_html=True,
                )
            with d3:
                st.markdown(
                    _delta_card_html("Gouvernance", analysis_n.get("delta_gov"),
                                     analysis_n.get("score_gov"), s_gov_n1),
                    unsafe_allow_html=True,
                )
            with d4:
                st.markdown(
                    _delta_card_html("Score Global", analysis_n.get("delta_global"),
                                     analysis_n.get("score_global"), s_gl_n1),
                    unsafe_allow_html=True,
                )

            # Graphique radar N vs N-1
            st.markdown("<br>", unsafe_allow_html=True)

            pillars = ["Env.", "Social", "Gov."]
            vals_n = [
                analysis_n.get("score_env") or 0,
                analysis_n.get("score_social") or 0,
                analysis_n.get("score_gov") or 0,
            ]
            vals_n1 = [
                analysis_n1.get("score_env") or 0,
                analysis_n1.get("score_social") or 0,
                analysis_n1.get("score_gov") or 0,
            ]

            col_radar2, col_bar2 = st.columns([1, 1])

            with col_radar2:
                st.markdown('<p class="section-title">Radar ESG N vs N-1</p>', unsafe_allow_html=True)
                fig_r = go.Figure()
                fig_r.add_trace(go.Scatterpolar(
                    r=vals_n1 + [vals_n1[0]],
                    theta=pillars + [pillars[0]],
                    fill="toself",
                    name=str(year_n1),
                    line=dict(color="#9CA3AF", width=2),
                    fillcolor="rgba(156,163,175,0.15)",
                ))
                fig_r.add_trace(go.Scatterpolar(
                    r=vals_n + [vals_n[0]],
                    theta=pillars + [pillars[0]],
                    fill="toself",
                    name=str(year_n),
                    line=dict(color="#1B3D20", width=2.5),
                    fillcolor="rgba(27,61,32,0.18)",
                ))
                fig_r.update_layout(
                    polar=dict(
                        radialaxis=dict(range=[0, 100], tickfont=dict(size=10, color="#6B7280"),
                                        gridcolor="#E5E7EB"),
                        angularaxis=dict(tickfont=dict(size=12, color="#374151", family="DM Sans")),
                        bgcolor="rgba(0,0,0,0)",
                    ),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    height=300,
                    margin=dict(t=20, b=20, l=20, r=20),
                    legend=dict(orientation="h", y=-0.08, font=dict(family="DM Sans", size=11)),
                    font=dict(family="DM Sans"),
                )
                st.plotly_chart(fig_r, use_container_width=True)

            with col_bar2:
                st.markdown('<p class="section-title">Comparaison scores piliers</p>', unsafe_allow_html=True)
                fig_cmp = go.Figure()
                fig_cmp.add_trace(go.Bar(
                    name=str(year_n1),
                    x=pillars,
                    y=vals_n1,
                    marker_color="#D1D5DB",
                    marker_line_width=0,
                ))
                fig_cmp.add_trace(go.Bar(
                    name=str(year_n),
                    x=pillars,
                    y=vals_n,
                    marker_color="#1B3D20",
                    marker_line_width=0,
                ))
                fig_cmp.update_layout(
                    barmode="group",
                    height=300,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    yaxis=dict(range=[0, 110], gridcolor="#F3F4F6", tickfont=dict(color="#6B7280")),
                    xaxis=dict(tickfont=dict(color="#374151", size=12)),
                    legend=dict(orientation="h", y=-0.15, font=dict(family="DM Sans", size=11)),
                    margin=dict(t=10, b=40, l=10, r=10),
                    font=dict(family="DM Sans"),
                )
                st.plotly_chart(fig_cmp, use_container_width=True)

            # Narration Delta (si disponible)
            narrative_raw = analysis_n.get("delta_narrative")
            if narrative_raw:
                try:
                    narrative = json.loads(narrative_raw) if isinstance(narrative_raw, str) else narrative_raw
                except Exception:
                    narrative = None

                if narrative:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown('<p class="section-title">Synthèse IA du delta</p>', unsafe_allow_html=True)

                    summary = narrative.get("delta_summary", "")
                    if summary:
                        st.markdown(
                            f'<div style="background:#F0FDF4;border:1.5px solid #86EFAC;border-radius:12px;'
                            f'padding:18px 20px;color:#14532D;font-size:0.92rem;line-height:1.6;">'
                            f'{summary}</div>',
                            unsafe_allow_html=True,
                        )

                    improvements = narrative.get("key_improvements") or []
                    regressions = narrative.get("key_regressions") or []
                    actions = narrative.get("priority_actions") or []

                    if improvements or regressions:
                        st.markdown("<br>", unsafe_allow_html=True)
                        col_imp, col_reg = st.columns(2)
                        with col_imp:
                            if improvements:
                                st.markdown(
                                    '<div style="font-weight:700;color:#065F46;'
                                    'font-size:0.85rem;margin-bottom:10px;">&#9650; Améliorations clés</div>',
                                    unsafe_allow_html=True,
                                )
                                for item in improvements:
                                    pillar = item.get("pillar", "")
                                    desc = item.get("description", "")
                                    st.markdown(
                                        f'<div style="background:#F0FDF4;border-radius:8px;'
                                        f'padding:10px 14px;margin-bottom:6px;font-size:0.85rem;">'
                                        f'<span style="background:#D1FAE5;color:#065F46;font-size:0.68rem;'
                                        f'font-weight:700;padding:1px 6px;border-radius:4px;">{pillar}</span>'
                                        f'<span style="color:#374151;margin-left:8px;">{desc}</span></div>',
                                        unsafe_allow_html=True,
                                    )
                        with col_reg:
                            if regressions:
                                st.markdown(
                                    '<div style="font-weight:700;color:#991B1B;'
                                    'font-size:0.85rem;margin-bottom:10px;">&#9660; Points de régression</div>',
                                    unsafe_allow_html=True,
                                )
                                for item in regressions:
                                    pillar = item.get("pillar", "")
                                    desc = item.get("description", "")
                                    st.markdown(
                                        f'<div style="background:#FEF2F2;border-radius:8px;'
                                        f'padding:10px 14px;margin-bottom:6px;font-size:0.85rem;">'
                                        f'<span style="background:#FEE2E2;color:#991B1B;font-size:0.68rem;'
                                        f'font-weight:700;padding:1px 6px;border-radius:4px;">{pillar}</span>'
                                        f'<span style="color:#374151;margin-left:8px;">{desc}</span></div>',
                                        unsafe_allow_html=True,
                                    )

                    if actions:
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown(
                            '<p class="section-title">Actions prioritaires recommandées</p>',
                            unsafe_allow_html=True,
                        )
                        for act in sorted(actions, key=lambda x: x.get("priority", 9)):
                            prio = act.get("priority", "?")
                            pillar = act.get("pillar", "")
                            action = act.get("action", "")
                            rationale = act.get("rationale", "")
                            colors_prio = {1: "#DC2626", 2: "#D97706", 3: "#2563EB", 4: "#059669", 5: "#6B7280"}
                            prio_color = colors_prio.get(prio, "#6B7280")
                            with st.expander(f"Priorité {prio} — [{pillar}] {action}"):
                                if rationale:
                                    st.markdown(
                                        f'<p style="color:#6B7280;font-size:0.85rem;">{rationale}</p>',
                                        unsafe_allow_html=True,
                                    )

st.markdown("<br>", unsafe_allow_html=True)


# HISTORIQUE DES ANALYSES
st.markdown('<p class="section-title">Historique des analyses</p>', unsafe_allow_html=True)

page = st.number_input("Page", min_value=1, value=1, step=1, label_visibility="collapsed")
per_page = 10

try:
    history_page = get_history(token, page=page, per_page=per_page)
except Exception:
    history_page = {"analyses": [], "total": 0, "page": 1, "per_page": per_page}

page_analyses = history_page.get("analyses", [])

def _status_badge(status):
    badges = {
        "success": ('<span style="background:#D1FAE5;color:#065F46;font-size:0.7rem;font-weight:700;'
                    'padding:2px 8px;border-radius:20px;">Terminé</span>'),
        "processing": ('<span style="background:#DBEAFE;color:#1E40AF;font-size:0.7rem;font-weight:700;'
                       'padding:2px 8px;border-radius:20px;">En cours</span>'),
        "pending": ('<span style="background:#F3F4F6;color:#6B7280;font-size:0.7rem;font-weight:700;'
                    'padding:2px 8px;border-radius:20px;">En attente</span>'),
        "failed": ('<span style="background:#FEE2E2;color:#991B1B;font-size:0.7rem;font-weight:700;'
                   'padding:2px 8px;border-radius:20px;">Échec</span>'),
    }
    return badges.get(status, status)

def _csrd_badge(csrd_ready):
    if csrd_ready is True:
        return '<span style="color:#065F46;font-weight:600;">&#10003; CSRD Ready</span>'
    if csrd_ready is False:
        return '<span style="color:#9CA3AF;">Non prêt</span>'
    return '<span style="color:#9CA3AF;">-</span>'

def _score_chip(score):
    if score is None:
        return '<span style="color:#9CA3AF;">-</span>'
    color = _score_color_hex(score)
    return (f'<span style="font-family:DM Serif Display,serif;font-size:1.1rem;'
            f'color:{color};font-weight:400;">{score:.0f}</span>'
            f'<span style="color:#9CA3AF;font-size:0.75rem;">/100</span>')

if page_analyses:
    # En-tête tableau
    h1, h2, h3, h4, h5, h6 = st.columns([2, 1, 1.2, 1.2, 1, 0.8])
    for col, label in zip([h1, h2, h3, h4, h5, h6],
                          ["Entreprise", "Année", "Score", "CSRD", "Statut", ""]):
        col.markdown(
            f'<div style="font-size:0.7rem;font-weight:700;color:#9CA3AF;'
            f'text-transform:uppercase;letter-spacing:0.07em;padding:4px 0;">{label}</div>',
            unsafe_allow_html=True,
        )

    for a in page_analyses:
        r1, r2, r3, r4, r5, r6 = st.columns([2, 1, 1.2, 1.2, 1, 0.8])
        with r1:
            st.markdown(
                f'<div style="font-weight:600;color:#111827;padding:8px 0;font-size:0.9rem;">'
                f'{a.get("company_name","?")}</div>',
                unsafe_allow_html=True,
            )
        with r2:
            st.markdown(
                f'<div style="color:#6B7280;padding:8px 0;font-size:0.88rem;">'
                f'{a.get("report_year","?")}</div>',
                unsafe_allow_html=True,
            )
        with r3:
            st.markdown(
                f'<div style="padding:8px 0;">{_score_chip(a.get("score_global"))}</div>',
                unsafe_allow_html=True,
            )
        with r4:
            st.markdown(
                f'<div style="padding:8px 0;font-size:0.82rem;">'
                f'{_csrd_badge(a.get("csrd_ready"))}</div>',
                unsafe_allow_html=True,
            )
        with r5:
            st.markdown(
                f'<div style="padding:8px 0;">{_status_badge(a.get("status","?"))}</div>',
                unsafe_allow_html=True,
            )
        with r6:
            if st.button("Voir", key=f"view_{a['id']}", use_container_width=True):
                save_last_analysis_id(a["id"])
                st.switch_page("pages/3_Resultats.py")
        st.markdown(
            '<hr style="margin:0;border-color:#F3F4F6;">',
            unsafe_allow_html=True,
        )

    total = history_page.get("total", 0)
    st.caption(f"Page {page} — {total} analyse(s) au total")

elif not all_analyses:
    st.markdown("""
    <div style="text-align:center;padding:40px 20px;background:white;
        border:1px solid #E5E7EB;border-radius:14px;">
        <div style="font-size:2.5rem;margin-bottom:12px;">📂</div>
        <div style="font-weight:600;color:#374151;font-size:1rem;margin-bottom:6px;">
            Aucune analyse pour le moment
        </div>
        <div style="color:#6B7280;font-size:0.88rem;">
            Lancez votre première analyse depuis la page Upload.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    col_cta1, col_cta2, col_cta3 = st.columns([2, 1, 2])
    with col_cta2:
        if st.button("Lancer une analyse", type="primary", use_container_width=True):
            st.switch_page("pages/2_Upload.py")
