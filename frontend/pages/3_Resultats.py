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

# --- IMPORT & INJECTION SEO ---
from frontend.components.seo import seo_for
seo_for("results")

from frontend.components.score_gauge import render_score_row
from frontend.components.esrs_coverage import render_esrs_grid
from frontend.components.delta_card import render_delta_row
from frontend.utils.api_client import APIError, get_analysis, download_pdf, download_delta_pdf, get_share_info
from frontend.components.analytics import track_event
from frontend.utils.session import get_token, get_last_analysis_id, require_auth

if not require_auth():
    st.stop()

token = get_token()
analysis_id = get_last_analysis_id()

# Sélection de l'analyse
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

# Chargement de l'analyse
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

# Vérifier le statut
status = analysis.get("status", "pending")

if status == "pending" or status == "processing":
    st.warning(f"L'analyse est en cours de traitement (status: {status}). Actualisez dans quelques instants.")
    if st.button("Actualiser"):
        st.rerun()
    st.stop()

if status == "failed":
    st.error(f"L'analyse a échoué : {analysis.get('error_message', 'Erreur inconnue')}")
    st.stop()

# RÉSULTATS (status = success)

st.markdown(
    f"""<div style="text-align: center; padding: 10px 0 20px 0;">
        <h2>Résultats de l'analyse #{analysis['id']}</h2>
        <p style="color: #6B7280;">
            Fichier : {analysis.get('source_filename', '?')} ·
            Année : {analysis.get('report_year', '?')} ·
            Temps : {analysis.get('processing_time_s', 0):.1f}s
        </p>
    </div>""",
    unsafe_allow_html=True,
)

# 1. Synthèse exécutive
summary = analysis.get("executive_summary")
if summary:
    st.info(f"**Synthèse exécutive**\n\n{summary}")

# 2. Scores E/S/G/Global (jauges)
score_env = analysis.get("score_env") or 0
score_social = analysis.get("score_social") or 0
score_gov = analysis.get("score_gov") or 0
score_global = analysis.get("score_global") or 0

render_score_row(score_env, score_social, score_gov, score_global)

# 3. Conformité CSRD
st.markdown("---")
csrd_ready = analysis.get("csrd_ready")
csrd_pct = analysis.get("csrd_coverage_pct")

if csrd_ready is not None:
    col_badge, col_pct = st.columns([1, 2])
    with col_badge:
        if csrd_ready:
            st.markdown(
                """<div style="background: #D4F0D8; border: 2px solid #1A3D22; border-radius: 12px;
                    padding: 20px; text-align: center;">
                    <div style="font-size: 36px;">&#10003;</div>
                    <div style="font-weight: 700; color: #1A3D22; font-size: 18px; margin-top: 8px;">
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

# 4. Couverture ESRS (grille)
st.markdown("---")
esrs_data = analysis.get("esrs_coverage")
render_esrs_grid(esrs_data)

# 5. KPIs détectés
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

# 6. Points forts & Lacunes
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

# 7. Recommandations
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

# 8. Delta (évolution vs précédent)
st.markdown("---")
render_delta_row(analysis)

# 8b. Bandeau upgrade (si plan gratuit)
user_info = None
try:
    from frontend.utils.session import get_user
    user_info = get_user()
except Exception:
    pass

user_plan = user_info.get("plan", "discovery") if user_info else "discovery"
is_free_plan = user_plan in ("discovery", "free")

if is_free_plan:
    st.markdown("---")
    st.markdown(
        """<div style="background: linear-gradient(135deg, #EFF6FF 0%, #F0FDF4 100%);
            border: 2px solid #1A3D22; border-radius: 16px; padding: 24px; text-align: center;
            margin: 10px 0;">
            <div style="font-size: 20px; font-weight: 700; color: #111827;">
                Débloquez le rapport PDF complet et le Delta Report
            </div>
            <div style="font-size: 14px; color: #6B7280; margin-top: 8px;">
                Avec le plan Essentiel (39€/analyse) ou Pro (129€/mois illimité),
                téléchargez vos rapports et suivez votre évolution ESG dans le temps.
            </div>
        </div>""",
        unsafe_allow_html=True,
    )
    col_upg1, col_upg2, col_upg3 = st.columns([1, 2, 1])
    with col_upg2:
        if st.button("Voir les tarifs", use_container_width=True, type="primary", key="results_upgrade"):
            st.switch_page("pages/6_Tarifs.py")

# 9. Boutons de téléchargement
st.markdown("---")
st.subheader("Téléchargements")

col_pdf, col_delta = st.columns(2)

with col_pdf:
    if is_free_plan:
        st.button(
            "Rapport PDF (plan Essentiel+)",
            use_container_width=True,
            type="primary",
            disabled=True,
            key="pdf_locked",
        )
        st.caption("Disponible à partir du plan Essentiel.")
    else:
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
        if is_free_plan:
            st.button(
                "Delta Report (plan Essentiel+)",
                use_container_width=True,
                disabled=True,
                key="delta_locked",
            )
            st.caption("Disponible à partir du plan Essentiel.")
        else:
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

# 10. Partage social (LinkedIn)
st.markdown("---")
st.subheader("Partager votre score")

try:
    share_info = get_share_info(token, analysis["id"])
    share_token = share_info.get("share_token", "")
    company = share_info.get("company_name", "Mon entreprise")
    score = share_info.get("score_global", 0)
    csrd = share_info.get("csrd_ready", False)
    year = share_info.get("report_year", "")

    # URL du badge (publique)
    import os
    app_url = os.getenv("APP_URL", "https://esg-optimizer.fr")
    badge_url = f"{app_url}/analysis/badge/{share_token}"

    # Texte pré-rempli pour LinkedIn
    csrd_text = "CSRD Ready ✓" if csrd else "en cours de conformité CSRD"
    linkedin_text = (
        f"Je viens d'analyser le rapport ESG {year} de {company} avec ESG Optimizer AI.\n\n"
        f"Score : {int(score)}/100 — {csrd_text}\n\n"
        f"Et vous, où en êtes-vous de votre conformité CSRD ?\n\n"
        f"Testez gratuitement → {app_url}"
    )

    import urllib.parse
    linkedin_share_url = (
        f"https://www.linkedin.com/sharing/share-offsite/"
        f"?url={urllib.parse.quote(app_url)}"
    )

    col_share, col_preview = st.columns([1, 1])

    with col_share:
        st.markdown(
            f"""<div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 12px;
                padding: 20px; text-align: center;">
                <div style="font-size: 13px; color: #6B7280; margin-bottom: 12px;">
                    Partagez votre score et boostez votre visibilité ESG
                </div>
                <div style="font-size: 11px; color: #9CA3AF; margin-top: 8px;">
                    Chaque partage = un backlink + preuve sociale
                </div>
            </div>""",
            unsafe_allow_html=True,
        )
        if st.link_button(
            "Partager sur LinkedIn",
            url=linkedin_share_url,
            use_container_width=True,
        ):
            pass
        track_event("share_linkedin", {"score": score, "company": company})

        # Texte à copier
        st.text_area(
            "Texte suggéré (copiez-collez)",
            value=linkedin_text,
            height=120,
            help="Copiez ce texte et collez-le dans votre post LinkedIn.",
        )

    with col_preview:
        st.markdown("**Aperçu du badge :**")
        st.markdown(
            f"""<div style="background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 12px;
                padding: 20px; text-align: center;">
                <div style="font-size: 48px; font-weight: 800; color: {'#1A3D22' if score >= 60 else '#F59E0B' if score >= 40 else '#EF4444'};">
                    {int(score)}<span style="font-size: 18px; color: #9CA3AF;">/100</span>
                </div>
                <div style="font-weight: 600; font-size: 14px; color: #111827; margin-top: 4px;">
                    {company}
                </div>
                <div style="margin-top: 8px;">
                    {'<span style="background:#D4F0D8; color:#1A3D22; padding:2px 10px; border-radius:8px; font-size:12px; font-weight:600;">CSRD Ready ✓</span>' if csrd else '<span style="background:#FEE2E2; color:#DC2626; padding:2px 10px; border-radius:8px; font-size:12px; font-weight:600;">Non conforme ✗</span>'}
                </div>
                <div style="font-size: 11px; color: #9CA3AF; margin-top: 8px;">
                    esg-optimizer.fr
                </div>
            </div>""",
            unsafe_allow_html=True,
        )
        # Lien direct vers l'image du badge
        st.caption(f"URL du badge : `{badge_url}`")

except APIError:
    st.caption("Partage non disponible pour cette analyse.")
except Exception:
    st.caption("Partage non disponible.")
