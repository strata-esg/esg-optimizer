"""
ESG Optimizer MVP — Page Upload & Analyse.
Upload d'un rapport ESG + lancement de l'analyse avec polling.
"""

import time
import streamlit as st
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from frontend.components.sidebar import render_sidebar
from frontend.utils.api_client import APIError, upload_analysis, get_analysis
from frontend.utils.session import get_token, require_auth, save_last_analysis_id

# ── Config page ──────────────────────────────────────────────────
st.set_page_config(page_title="Upload — ESG Optimizer", page_icon="📤", layout="centered")
render_sidebar()

if not require_auth():
    st.stop()

# ── Header ───────────────────────────────────────────────────────
st.markdown(
    """<div style="text-align: center; padding: 20px 0;">
        <h2>📤 Nouvelle Analyse ESG</h2>
        <p style="color: #6B7280;">Uploadez un rapport de durabilité pour obtenir votre analyse en quelques minutes.</p>
    </div>""",
    unsafe_allow_html=True,
)

# ── Formulaire d'upload ──────────────────────────────────────────
uploaded_file = st.file_uploader(
    "Rapport de durabilité",
    type=["pdf", "docx", "xlsx"],
    help="Formats acceptés : PDF, Word (DOCX), Excel (XLSX). Taille max : 20 MB.",
)

col1, col2 = st.columns(2)
with col1:
    company_name = st.text_input(
        "Nom de l'entreprise analysée",
        placeholder="Ex: GreenTech SAS",
    )
with col2:
    report_year = st.number_input(
        "Année du rapport",
        min_value=2000,
        max_value=2100,
        value=2024,
        step=1,
    )

sector = st.selectbox(
    "Secteur d'activité (optionnel)",
    options=[
        None,
        "Énergie",
        "Industrie manufacturière",
        "Construction & BTP",
        "Transport & Logistique",
        "Agriculture & Agroalimentaire",
        "Services financiers",
        "Technologies & Télécoms",
        "Santé & Pharma",
        "Commerce & Distribution",
        "Immobilier",
        "Tourisme & Hôtellerie",
        "Autre",
    ],
    format_func=lambda x: "— Sélectionner un secteur —" if x is None else x,
)

# ── Bouton Analyser ──────────────────────────────────────────────
can_submit = uploaded_file is not None and company_name.strip() != ""

if st.button(
    "Analyser le rapport",
    disabled=not can_submit,
    use_container_width=True,
    type="primary",
):
    token = get_token()
    if not token:
        st.error("Session expirée, veuillez vous reconnecter.")
        st.stop()

    try:
        # 1. Upload du fichier
        with st.spinner("Upload du fichier..."):
            result = upload_analysis(
                token=token,
                file_bytes=uploaded_file.getvalue(),
                filename=uploaded_file.name,
                company_name=company_name.strip(),
                report_year=int(report_year),
                sector=sector,
            )

        analysis_id = result["analysis_id"]
        save_last_analysis_id(analysis_id)

        st.success(f"Analyse #{analysis_id} lancée !")

        # 2. Polling — attendre la fin de l'analyse
        status_container = st.empty()
        progress_bar = st.progress(0, text="Extraction du texte...")

        poll_count = 0
        max_polls = 60  # 60 x 3s = 3 minutes max

        while poll_count < max_polls:
            time.sleep(3)
            poll_count += 1

            try:
                analysis = get_analysis(token, analysis_id)
            except APIError:
                continue

            current_status = analysis.get("status", "pending")

            if current_status == "pending":
                progress_bar.progress(10, text="En attente de traitement...")
            elif current_status == "processing":
                pct = min(20 + (poll_count * 3), 90)
                progress_bar.progress(pct, text="Analyse GPT-4o en cours...")
            elif current_status == "success":
                progress_bar.progress(100, text="Analyse terminée !")
                status_container.success("Analyse terminée avec succès !")
                time.sleep(1)
                st.page_link(
                    "pages/3_Resultats.py",
                    label="Voir les résultats",
                    icon="📊",
                    use_container_width=True,
                )
                st.rerun()
            elif current_status == "failed":
                progress_bar.empty()
                error_msg = analysis.get("error_message", "Erreur inconnue")
                status_container.error(f"L'analyse a échoué : {error_msg}")
                break

        else:
            progress_bar.empty()
            status_container.warning(
                "L'analyse prend plus de temps que prévu. "
                "Vérifiez les résultats dans quelques minutes via le Dashboard."
            )

    except APIError as e:
        st.error(f"Erreur : {e.detail}")
    except Exception as e:
        st.error(f"Erreur inattendue : {e}")

# ── Aide ─────────────────────────────────────────────────────────
if not can_submit:
    st.caption("Uploadez un fichier et renseignez le nom de l'entreprise pour lancer l'analyse.")

with st.expander("Comment ça marche ?"):
    st.markdown(
        """1. **Upload** — Déposez votre rapport de durabilité (PDF, Word ou Excel)
2. **Extraction** — Le texte est extrait automatiquement du document
3. **Analyse IA** — GPT-4o analyse le contenu selon les standards ESRS/CSRD
4. **Résultats** — Scores E/S/G, conformité CSRD, KPIs détectés, recommandations
5. **Rapport PDF** — Téléchargez un rapport professionnel prêt à partager"""
    )
