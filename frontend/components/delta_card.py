"""
ESG Optimizer MVP - Composant carte delta avec indicateur de tendance.
Affiche le delta entre deux analyses (flèches, couleurs, valeur).
"""

import json
import streamlit as st


def _trend_icon(delta: float) -> tuple[str, str, str]:
    """
    Retourne (icône, couleur, label) selon le delta.
    """
    if delta > 5:
        return "&#9650;", "#1A3D22", "Forte amélioration"
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
    if not narrative:
        return

    st.markdown("---")

    # Parser le JSON (stocké en string dans la DB)
    if isinstance(narrative, str):
        try:
            data = json.loads(narrative)
        except (json.JSONDecodeError, ValueError):
            st.info(narrative)
            return
    else:
        data = narrative

    # 1. Résumé global
    summary = data.get("delta_summary", "")
    if summary:
        st.markdown("**Synthèse d'évolution**")
        st.info(summary)

    # 2. Évolution ESRS
    esrs = data.get("esrs_evolution", {})
    gained = esrs.get("gained") or []
    lost = esrs.get("lost") or []
    cov_prev = esrs.get("coverage_previous")
    cov_curr = esrs.get("coverage_current")

    if gained or lost or (cov_prev is not None and cov_curr is not None):
        st.markdown("**Couverture ESRS**")
        col_g, col_l = st.columns(2)
        with col_g:
            if cov_curr is not None and cov_prev is not None:
                delta_cov = round(cov_curr - cov_prev, 1)
                color_cov = "#1A3D22" if delta_cov >= 0 else "#EF4444"
                st.markdown(
                    f'<div style="font-size:13px;color:#374151;">Couverture : '
                    f'<b style="color:{color_cov};">{cov_curr:.0f}%</b> '
                    f'<span style="color:{color_cov};">({delta_cov:+.1f}% vs avant)</span></div>',
                    unsafe_allow_html=True,
                )
            if gained:
                st.markdown("**Nouveaux standards couverts**")
                for g in gained:
                    st.markdown(f'<span style="color:#1A3D22;">&#10003;</span> `{g}`', unsafe_allow_html=True)
        with col_l:
            if lost:
                st.markdown("**Standards perdus**")
                for l in lost:
                    st.markdown(f'<span style="color:#EF4444;">&#10007;</span> `{l}`', unsafe_allow_html=True)

    # 3. Comparaison KPIs
    kpis = data.get("kpi_comparison") or []
    if kpis:
        st.markdown("**Évolution des KPIs**")
        new_kpis = [k for k in kpis if k.get("status") == "new"]
        removed_kpis = [k for k in kpis if k.get("status") == "removed"]
        changed_kpis = [k for k in kpis if k.get("status") == "changed"]

        col_new, col_rem = st.columns(2)
        with col_new:
            if new_kpis:
                st.markdown('<span style="color:#1A3D22;font-weight:600;">Nouveaux KPIs</span>', unsafe_allow_html=True)
                for k in new_kpis:
                    val = f"{k.get('current_value')} {k.get('unit','')}" if k.get('current_value') else ""
                    st.markdown(f"+ **{k['name']}** {val}")
        with col_rem:
            if removed_kpis:
                st.markdown('<span style="color:#EF4444;font-weight:600;">KPIs supprimés</span>', unsafe_allow_html=True)
                for k in removed_kpis:
                    val = f"{k.get('previous_value')} {k.get('unit','')}" if k.get('previous_value') else ""
                    st.markdown(f"- **{k['name']}** {val}")
        if changed_kpis:
            st.markdown("**KPIs modifiés**")
            for k in changed_kpis:
                st.markdown(f"· **{k['name']}** : {k.get('previous_value','?')} -> {k.get('current_value','?')} {k.get('unit','')}")

    # 4. Points d'amélioration & régressions
    improvements = data.get("key_improvements") or []
    regressions = data.get("key_regressions") or []
    if improvements or regressions:
        st.markdown("**Points clés**")
        col_imp, col_reg = st.columns(2)
        with col_imp:
            if improvements:
                st.markdown('<span style="color:#1A3D22;font-weight:600;">Améliorations</span>', unsafe_allow_html=True)
                for item in improvements:
                    pillar = item.get("pillar", "")
                    desc = item.get("description", "")
                    st.markdown(f'<div style="font-size:13px;margin-bottom:4px;">'
                                f'<span style="background:#D4F0D8;color:#1A3D22;padding:1px 6px;'
                                f'border-radius:4px;font-size:11px;font-weight:700;">{pillar}</span> {desc}</div>',
                                unsafe_allow_html=True)
        with col_reg:
            if regressions:
                st.markdown('<span style="color:#EF4444;font-weight:600;">Régressions</span>', unsafe_allow_html=True)
                for item in regressions:
                    pillar = item.get("pillar", "")
                    desc = item.get("description", "")
                    st.markdown(f'<div style="font-size:13px;margin-bottom:4px;">'
                                f'<span style="background:#FEE2E2;color:#991B1B;padding:1px 6px;'
                                f'border-radius:4px;font-size:11px;font-weight:700;">{pillar}</span> {desc}</div>',
                                unsafe_allow_html=True)

    # 5. Actions prioritaires
    actions = data.get("priority_actions") or []
    if actions:
        st.markdown("**Actions prioritaires**")
        for act in sorted(actions, key=lambda x: x.get("priority", 9)):
            prio = act.get("priority", "?")
            pillar = act.get("pillar", "")
            action = act.get("action", "")
            rationale = act.get("rationale", "")
            with st.expander(f"Priorité {prio} - [{pillar}] {action}"):
                if rationale:
                    st.caption(rationale)
