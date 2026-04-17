"""
ESG Optimizer MVP — Page Résultats.
Affichage complet d'une analyse ESG : scores, ESRS, KPIs, recommandations, deltas.
"""

import pandas as pd
import streamlit as st
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from frontend.components.sidebar import render_sidebar
from frontend.components.score_gauge import render_score_row
from frontend.components.esrs_coverage import render_esrs_grid
from frontend.components.delta_card import render_delta_row
from frontend.utils.api_client import APIError, get_analysis, download_pdf, download_delta_pdf
from frontend.utils.session import get_token, get_last_analysis_id, require_auth

# ── Config page ──────────────────────────────────────────────────
st.set_page_config(page_title="Résultats — ESG Optimizer", page_icon="📊", layout="wide")
render_sidebar()

if not require_auth():
    st.stop()

token = get_token()
analysis_id = get_last_analysis_id()

# ── Sélection de l'analyse ───────────────────────────────────────
col_id, col_btn = st.columns([3, 1])
with col_id:
    manual_id = st.number_input(
        "ID de l'analyse",
        min_value=1,
        value=analysis_id or 1,
        step=1,
        help="Entrez l'ID de l'analyse à consulter.",
    )
with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    load_btn = st.button("Charger", use_container_width=True, type="primary")

# Charger automatiquement si on arrive de l'upload, sinon sur clic
should_load = load_btn or (analysis_id is not None and "analysis_loaded" not in st.session_state)

if not should_load:
    st.info("Entrez un ID d'analyse et cliquez sur Charger, ou lancez une nouvelle analyse depuis Upload.")
    st.stop()

# ── Chargement de l'analyse ──────────────────────────────────────
try:
    with st.spinner("Chargement de l'analyse..."):
        analysis = get_analysis(token, int(manual_id))
    st.session_state["analysis_loaded"] = True
except APIError as e:
    st.error(f"Erreur : {e.detail}")
    st.stop()
except Exception as e:
    st.error(f"Impossible de charger l'analyse : {e}")
    st.stop()

# ── Vérifier le statut ──────────────────────────────────────────
status = analysis.get("status", "pending")

if status == "pending" or status == "processing":
    st.warning(f"L'analyse est en cours de traitement (status: {status}). Actualisez dans quelques instants.")
    if st.button("Actualiser"):
        st.rerun()
    st.stop()

if status == "failed":
    st.error(f"L'analyse a échoué : {analysis.get('error_message', 'Erreur inconnue')}")
    st.stop()

# ══════════════════════════════════════════════════════════════════
# RÉSULTATS (status = success)
# ══════════════════════════════════════════════════════════════════

st.markdown(
    f"""<div style="text-align: center; padding: 10px 0 20px 0;">
        <h2>📊 Résultats de l'analyse #{analysis['id']}</h2>
        <p style="color: #6B7280;">
            Fichier : {analysis.get('source_filename', '?')} ·
            Année : {analysis.get('report_year', '?')} ·
            Temps : {analysis.get('processing_time_s', 0):.1f}s
        </p>
    </div>""",
    unsafe_allow_html=True,
)

# ── 1. Synthèse exécutive ────────────────────────────────────────
summary = analysis.get("executive_summary")
if summary:
    st.info(f"**Synthèse exécutive**\n\n{summary}")

# ── 2. Scores E/S/G/Global (jauges) ─────────────────────────────
score_env = analysis.get("score_env") or 0
score_social = analysis.get("score_social") or 0
score_gov = analysis.get("score_gov") or 0
score_global = analysis.get("score_global") or 0

render_score_row(score_env, score_social, score_gov, score_global)

# ── 3. Conformité CSRD ──────────────────────────────────────────
st.markdown("---")
csrd_ready = analysis.get("csrd_ready")
csrd_pct = analysis.get("csrd_coverage_pct")

if csrd_ready is not None:
    col_badge, col_pct = st.columns([1, 2])
    with col_badge:
        if csrd_ready:
            st.markdown(
                """<div style="background: #D1FAE5; border: 2px solid #10B981; border-radius: 12px;
                    padding: 20px; text-align: center;">
                    <div style="font-size: 36px;">&#10003;</div>
                    <div style="font-weight: 700; color: #065F46; font-size: 18px; margin-top: 8px;">
                        CSRD Ready
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """<div style="background: #FEE2E2; border: 2px solid #EF4444; border-radius: 12px;
                    padding: 20px; text-align: center;">
                    <div style="font-size: 36px;">&#10007;</div>
                    <div style="font-weight: 700; color: #991B1B; font-size: 18px; margin-top: 8px;">
                        Non conforme CSRD
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )
    with col_pct:
        if csrd_pct is not None:
            st.metric("Couverture CSRD", f"{csrd_pct:.0f}%")
        missing = analysis.get("missing_disclosures") or []
        if missing:
            st.markdown("**Disclosures manquantes :**")
            for m in missing:
                st.markdown(f"- {m}")

# ── 4. Couverture ESRS (grille) ─────────────────────────────────
st.markdown("---")
esrs_data = analysis.get("esrs_coverage")
render_esrs_grid(esrs_data)

# ── 5. KPIs détectés ────────────────────────────────────────────
st.markdown("---")
kpis = analysis.get("kpis_detected") or []
if kpis:
    st.subheader("KPIs détectés")
    kpi_df = pd.DataFrame(kpis)
    if not kpi_df.empty:
        # Réordonner les colonnes si elles existent
        desired_cols = ["pillar", "name", "value", "unit", "esrs_reference"]
        existing_cols = [c for c in desired_cols if c in kpi_df.columns]
        kpi_df = kpi_df[existing_cols]
        kpi_df.columns = [
            {"pillar": "Pilier", "name": "Indicateur", "value": "Valeur",
             "unit": "Unité", "esrs_reference": "Réf. ESRS"}.get(c, c)
            for c in kpi_df.columns
        ]
        st.dataframe(kpi_df, use_container_width=True, hide_index=True)
else:
    st.caption("Aucun KPI détecté dans le rapport.")

# ── 6. Points forts & Lacunes ────────────────────────────────────
st.markdown("---")
col_str, col_weak = st.columns(2)

strengths = analysis.get("strengths") or []
weaknesses = analysis.get("weaknesses") or []

with col_str:
    st.subheader("Points forts")
    if strengths:
        for s in strengths:
            pillar = s.get("pillar", "?")
            desc = s.get("description", "")
            st.markdown(f"**[{pillar}]** {desc}")
    else:
        st.caption("Aucun point fort identifié.")

with col_weak:
    st.subheader("Lacunes")
    if weaknesses:
        for w in weaknesses:
            pillar = w.get("pillar", "?")
            desc = w.get("description", "")
            st.markdown(f"**[{pillar}]** {desc}")
    else:
        st.caption("Aucune lacune identifiée.")

# ── 7. Recommandations ──────────────────────────────────────────
st.markdown("---")
recommendations = analysis.get("recommendations") or []
if recommendations:
    st.subheader("Recommandations")
    # Trier par priorité
    sorted_recs = sorted(recommendations, key=lambda r: r.get("priority", 5))
    for rec in sorted_recs:
        prio = rec.get("priority", "?")
        pillar = rec.get("pillar", "?")
        action = rec.get("action", "")
        impact = rec.get("expected_impact", "")
        esrs_ref = rec.get("esrs_reference", "")

        with st.expander(f"Priorité {prio} — [{pillar}] {action}"):
            if impact:
                st.markdown(f"**Impact attendu** : {impact}")
            if esrs_ref:
                st.markdown(f"**Référence ESRS** : {esrs_ref}")

# ── 8. Delta (évolution vs précédent) ───────────────────────────
st.markdown("---")
render_delta_row(analysis)

# ── 9. Boutons de téléchargement ─────────────────────────────────
st.markdown("---")
st.subheader("Téléchargements")

col_pdf, col_delta = st.columns(2)

with col_pdf:
    if st.button("Télécharger le rapport PDF", use_container_width=True, type="primary"):
        try:
            with st.spinner("Génération du PDF..."):
                pdf_bytes = download_pdf(token, analysis["id"])
            st.download_button(
                label="Enregistrer le PDF",
                data=pdf_bytes,
                file_name=f"ESG_Report_{analysis['id']}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except APIError as e:
            st.error(f"Erreur : {e.detail}")

with col_delta:
    has_delta = analysis.get("delta_narrative") is not None
    if has_delta:
        if st.button("Télécharger le Delta Report PDF", use_container_width=True):
            try:
                with st.spinner("Génération du delta PDF..."):
                    delta_bytes = download_delta_pdf(token, analysis["id"])
                st.download_button(
                    label="Enregistrer le Delta PDF",
                    data=delta_bytes,
                    file_name=f"ESG_Delta_{analysis['id']}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except APIError as e:
                st.error(f"Erreur : {e.detail}")
    else:
        st.caption("Pas de delta disponible (première analyse de cette entreprise).")
