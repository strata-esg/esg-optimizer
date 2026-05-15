"""
ESG Optimizer MVP - Page Résultats.
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
from frontend.utils.api_client import APIError, get_analysis, download_pdf, download_delta_pdf, download_preview_pdf, get_share_info, recompute_delta
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

# Charger si :
#   - l'utilisateur vient de cliquer sur "Charger"
#   - on arrive depuis l'upload (analysis_id présent et première visite)
#   - l'analyse était déjà chargée (rerun causé par un clic de bouton sur la page)
#   Sans la 3e condition, tout st.button (PDF, delta…) déclenche un rerun ->
#   should_load = False -> st.stop() s'exécute avant le code de téléchargement.
should_load = (
    load_btn
    or (analysis_id is not None and "analysis_loaded" not in st.session_state)
    or "analysis_loaded" in st.session_state
)

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

if csrd_pct is not None:
    col_badge, col_pct = st.columns([1, 2])
    with col_badge:
        # 4 niveaux CSRD basés sur csrd_coverage_pct (pas sur le booléen LLM)
        if csrd_pct == 100:
            badge_html = (
                '<div style="background:#D4F0D8; border:2px solid #1B3D20; border-radius:12px;'
                'padding:20px; text-align:center;">'
                '<div style="font-size:34px; color:#1B3D20;">&#10003;</div>'
                '<div style="font-weight:700; color:#1B3D20; font-size:17px; margin-top:6px;">CSRD Ready</div>'
                '<div style="font-size:11px; color:#2A5C34; margin-top:4px; letter-spacing:.04em; text-transform:uppercase;">Couverture 100 %</div>'
                '</div>'
            )
        elif csrd_pct >= 80:
            badge_html = (
                f'<div style="background:#DBEAFE; border:2px solid #2563EB; border-radius:12px;'
                f'padding:20px; text-align:center;">'
                f'<div style="font-size:34px; color:#1D4ED8;">&#9651;</div>'
                f'<div style="font-weight:700; color:#1E40AF; font-size:15px; margin-top:6px;">Conformité Avancée</div>'
                f'<div style="font-size:11px; color:#3B82F6; margin-top:4px; text-transform:uppercase; letter-spacing:.04em;">'
                f'Couverture {csrd_pct:.0f} % - 100 % requis</div>'
                f'</div>'
            )
        elif csrd_pct >= 50:
            badge_html = (
                f'<div style="background:#FFF7ED; border:2px solid #EA580C; border-radius:12px;'
                f'padding:20px; text-align:center;">'
                f'<div style="font-size:34px; color:#EA580C;">&#9680;</div>'
                f'<div style="font-weight:700; color:#9A3412; font-size:14px; margin-top:6px;">En cours de structuration</div>'
                f'<div style="font-size:11px; color:#C2410C; margin-top:4px; text-transform:uppercase; letter-spacing:.04em;">'
                f'Couverture {csrd_pct:.0f} % - efforts requis</div>'
                f'</div>'
            )
        else:
            badge_html = (
                f'<div style="background:#FEE2E2; border:2px solid #DC2626; border-radius:12px;'
                f'padding:20px; text-align:center;">'
                f'<div style="font-size:34px; color:#DC2626;">&#10007;</div>'
                f'<div style="font-weight:700; color:#991B1B; font-size:15px; margin-top:6px;">Lacunes majeures</div>'
                f'<div style="font-size:11px; color:#991B1B; margin-top:4px; text-transform:uppercase; letter-spacing:.04em;">'
                f'Couverture {csrd_pct:.0f} % - restructuration nécessaire</div>'
                f'</div>'
            )
        st.markdown(badge_html, unsafe_allow_html=True)

    with col_pct:
        st.metric(
            "Couverture CSRD",
            f"{csrd_pct:.0f}%",
            help="100% = CSRD Ready · 80-99% = Conformité Avancée · 50-79% = En cours · <50% = Lacunes majeures",
        )
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

    # Red flags Gouvernance si score G < 60
    if score_gov < 60:
        sev = "critique" if score_gov < 40 else "élevée"
        sev_color = "#991B1B" if score_gov < 40 else "#92400E"
        sev_bg = "#FEE2E2" if score_gov < 40 else "#FEF3C7"
        sev_border = "#EF4444" if score_gov < 40 else "#F59E0B"
        st.markdown(
            f"""<div style="background:{sev_bg}; border-left:4px solid {sev_border};
                border-radius:0 8px 8px 0; padding:12px 14px; margin-top:12px;">
                <div style="font-weight:700; color:{sev_color}; font-size:13px; margin-bottom:6px;">
                    ⚠ Alerte Gouvernance - Sévérité {sev} (G : {int(score_gov)}/100)
                </div>
                <div style="font-size:12px; color:{sev_color}; line-height:1.6;">
                    {"-> Score G < 40 : reporting de gouvernance quasi absent. Les auditeurs CSRD exigeront a minima :<br>- Politique anti-corruption documentée (ESRS G1)<br>- Déclaration sur la conformité fiscale<br>- Dispositif de protection des lanceurs d'alerte" if score_gov < 40 else
                     "-> Score G < 60 : plusieurs indicateurs G1 manquants.<br>- Vérifier la présence d'une charte éthique publiée<br>- Documenter les procédures de due diligence fournisseurs<br>- Préciser les objectifs chiffrés de lutte contre la corruption"}
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

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

        with st.expander(f"Priorité {prio} - [{pillar}] {action}"):
            if impact:
                st.markdown(f"**Impact attendu** : {impact}")
            if esrs_ref:
                st.markdown(f"**Référence ESRS** : {esrs_ref}")

# 8. Delta (évolution vs précédent)
st.markdown("---")
render_delta_row(analysis)

# 8b. Bandeau upgrade (si plan gratuit)
# On récupère le plan FRAIS depuis l'API (pas le cache session qui peut être stale après upgrade Stripe)
user_info = None
try:
    from frontend.utils.api_client import get_me
    from frontend.utils.session import save_user
    user_info = get_me(token)
    save_user(user_info)   # met à jour le cache session pour la sidebar etc.
except Exception:
    from frontend.utils.session import get_user
    user_info = get_user()

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
        # FIX : st.page_link = ancre HTML directe, pas de rerun intermédiaire qui court-circuite la page
        st.page_link("pages/6_Tarifs.py", label="🔓 Voir les tarifs", use_container_width=True)

# 9. Boutons de téléchargement
st.markdown("---")
st.subheader("Téléchargements")

col_pdf, col_delta = st.columns(2)

with col_pdf:
    if is_free_plan:
        # Plan Découverte : aperçu 3 pages watermarked disponible
        if st.button("📄 Télécharger l'aperçu PDF (3 pages)", use_container_width=True, key="pdf_preview"):
            try:
                with st.spinner("Génération de l'aperçu PDF..."):
                    preview_bytes = download_preview_pdf(token, analysis["id"])
                st.download_button(
                    label="⬇ Enregistrer l'aperçu (watermark)",
                    data=preview_bytes,
                    file_name=f"ESG_Preview_{analysis['id']}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except APIError as e:
                st.error(f"Erreur : {e.detail}")
        st.caption("Aperçu 3 pages avec mention PRÉVISUALISATION. Le rapport complet (8+ pages) est disponible à partir du plan Essentiel.")
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
        if not is_free_plan:
            # Plan payant mais delta pas encore calculé : bouton de recalcul
            if st.button("Calculer le Delta Report", use_container_width=True, key="recompute_delta"):
                try:
                    with st.spinner("Calcul du delta en cours (30-60s)..."):
                        recompute_delta(token, analysis["id"])
                    st.success("Delta calculé ! Rechargez la page.")
                    st.rerun()
                except APIError as e:
                    if "introuvable" in e.detail.lower():
                        st.caption("Pas de delta disponible (première analyse de cette entreprise).")
                    else:
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

    # Badge CSRD 4 niveaux (basé sur csrd_pct déjà chargé, plus fiable que le booléen LLM)
    _share_pct = csrd_pct  # déjà en scope depuis l'analyse principale
    if _share_pct is not None:
        if _share_pct >= 100:
            _badge_label, _badge_style = "CSRD Ready ✓", "background:#D4F0D8;color:#1A3D22;"
            csrd_text = "CSRD Ready ✓"
        elif _share_pct >= 80:
            _badge_label, _badge_style = "Conformité Avancée", "background:#DBEAFE;color:#1E40AF;"
            csrd_text = f"Conformité Avancée ({int(_share_pct)}% CSRD)"
        elif _share_pct >= 50:
            _badge_label, _badge_style = "En cours de structuration", "background:#FFF7ED;color:#9A3412;"
            csrd_text = "en cours de conformité CSRD"
        else:
            _badge_label, _badge_style = "Lacunes majeures", "background:#FEE2E2;color:#991B1B;"
            csrd_text = "avec des lacunes CSRD importantes"
    else:
        _badge_label = "CSRD Ready ✓" if csrd else "Non conforme ✗"
        _badge_style = "background:#D4F0D8;color:#1A3D22;" if csrd else "background:#FEE2E2;color:#DC2626;"
        csrd_text = "CSRD Ready ✓" if csrd else "en cours de conformité CSRD"
    linkedin_text = (
        f"Je viens d'analyser le rapport ESG {year} de {company} avec ESG Optimizer AI.\n\n"
        f"Score : {int(score)}/100 - {csrd_text}\n\n"
        f"Et vous, où en êtes-vous de votre conformité CSRD ?\n\n"
        f"Testez gratuitement -> {app_url}"
    )

    import urllib.parse
    linkedin_share_url = (
        f"https://www.linkedin.com/sharing/share-offsite/"
        f"?url={urllib.parse.quote(app_url)}"
    )

    col_share, col_preview = st.columns([1, 1])

    with col_share:
        # FIX #10 : copywriting orienté valorisation de marque, sans jargon technique
        st.markdown(
            f"""<div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 12px;
                padding: 20px; text-align: center;">
                <div style="font-size: 14px; font-weight: 600; color: #1E40AF; margin-bottom: 8px;">
                    Valorisez votre démarche RSE
                </div>
                <div style="font-size: 13px; color: #6B7280; margin-bottom: 8px;">
                    Montrez à vos parties prenantes, clients et partenaires
                    que votre entreprise s'engage concrètement pour la durabilité.
                </div>
                <div style="font-size: 12px; color: #93C5FD; font-style: italic;">
                    Un score publié, c'est une preuve de transparence qui renforce votre crédibilité ESG.
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
        # Couleur d'accent selon le score
        _score_color = "#1A3D22" if score >= 60 else "#D97706" if score >= 40 else "#DC2626"
        _accent_bg = "#D4F0D8" if score >= 60 else "#FEF3C7" if score >= 40 else "#FEE2E2"
        st.markdown(
            f"""<div style="position:relative;
                background: linear-gradient(135deg, #FFFFFF 0%, #F7F2E8 100%);
                border: 1.5px solid {_score_color};
                border-radius: 18px;
                padding: 24px 22px 22px 22px;
                text-align: center;
                box-shadow: 0 8px 24px rgba(26,61,34,0.08), 0 2px 4px rgba(26,61,34,0.04);
                overflow: hidden;">
                <!-- Filigrane décoratif -->
                <div style="position:absolute; top:-24px; right:-24px; width:120px; height:120px;
                    background: radial-gradient(circle, {_accent_bg} 0%, transparent 70%);
                    border-radius: 50%; opacity: 0.55; pointer-events: none;"></div>
                <!-- Logo ESG -->
                <div style="display:flex; align-items:center; justify-content:center; gap:8px;
                    margin-bottom: 14px;">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"
                         width="22" height="22">
                        <circle cx="20" cy="20" r="19" fill="#1A3D22"/>
                        <path d="M 8,24 A 12,12 0 1,1 32,24"
                            stroke="rgba(212,240,216,0.3)" stroke-width="2.5"
                            stroke-linecap="round" fill="none"/>
                        <path d="M 8,24 A 12,12 0 0,1 27,11"
                            stroke="#7FC686" stroke-width="2.5"
                            stroke-linecap="round" fill="none"/>
                        <circle cx="20" cy="22" r="2" fill="#D4F0D8"/>
                        <line x1="20" y1="22" x2="29" y2="11"
                            stroke="#D4F0D8" stroke-width="1.8" stroke-linecap="round"/>
                    </svg>
                    <span style="font-family:'DM Sans',sans-serif; font-size:11px;
                        font-weight:700; color:#1A3D22; letter-spacing:0.12em;
                        text-transform:uppercase;">ESG Optimizer</span>
                </div>
                <!-- Score géant typé serif -->
                <div style="font-family:'DM Serif Display',Georgia,serif;
                    font-size: 5rem; font-weight:400; line-height:1;
                    color: {_score_color}; letter-spacing: -0.04em;">
                    {int(score)}<span style="font-family:'DM Sans',sans-serif;
                        font-size: 1.3rem; color:#9CA3AF; font-weight:400;">/100</span>
                </div>
                <!-- Label score -->
                <div style="font-family:'DM Sans',sans-serif; font-size:10px;
                    color:#6B7280; text-transform:uppercase; letter-spacing:0.1em;
                    margin: 4px 0 14px;">
                    Score ESG global
                </div>
                <!-- Entreprise -->
                <div style="font-family:'DM Serif Display',Georgia,serif;
                    font-weight:400; font-size: 16px; color:#111827;
                    letter-spacing:-0.01em; margin-bottom: 4px;">
                    {company}
                </div>
                <div style="font-size: 11px; color:#9CA3AF; margin-bottom: 12px;">
                    Rapport {year}
                </div>
                <!-- Badge conformité -->
                <div style="margin: 6px 0 14px;">
                    <span style="{_badge_style}padding:6px 14px;border-radius:20px;
                        font-family:'DM Sans',sans-serif; font-size:12px;
                        font-weight:600; letter-spacing:0.02em;">{_badge_label}</span>
                </div>
                <!-- Footer URL -->
                <div style="border-top:1px solid #E5E7EB; padding-top:10px;
                    font-family:'DM Sans',sans-serif; font-size:10.5px;
                    color:#6B7280; letter-spacing:0.04em;">
                    Vérifié par <strong style="color:#1A3D22;">esg-optimizer.fr</strong>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )
        # Lien direct vers l'image du badge
        st.caption(f"URL du badge partageable : `{badge_url}`")

except APIError:
    st.caption("Partage non disponible pour cette analyse.")
except Exception:
    st.caption("Partage non disponible.")
