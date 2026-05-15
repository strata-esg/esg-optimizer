"""
ESG Optimizer MVP - Page Upload & Analyse.
Upload d'un rapport ESG + lancement de l'analyse avec polling.
"""

import time
import streamlit as st
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

# --- IMPORT & INJECTION SEO ---
from frontend.components.seo import seo_for # Utilise seo_for ou inject_seo selon ton fichier utilitaire
seo_for("upload")

from frontend.utils.api_client import APIError, upload_analysis, get_analysis
from frontend.utils.session import get_token, get_user, require_auth, save_last_analysis_id
from frontend.components.analytics import track_upload_started, track_analysis_completed

if not require_auth():
    st.stop()

# CSS du dropzone + JS de traduction des textes Streamlit anglais
st.markdown(
    """
    <style>
    [data-testid="stFileUploaderDropzone"] {
        background: #FFFFFF !important;
        border: 2px dashed #4DB862 !important;
        border-radius: 14px !important;
        padding: 28px 20px !important;
        transition: border-color 0.2s ease, background 0.2s ease !important;
    }
    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: #1B3D20 !important;
        background: #F0FAF0 !important;
    }
    [data-testid="stFileUploaderDropzone"] p,
    [data-testid="stFileUploaderDropzone"] span,
    [data-testid="stFileUploaderDropzone"] small {
        font-family: 'DM Sans', sans-serif !important;
        color: #6B7280 !important;
    }
    /* Masquer "Press Enter to submit form" */
    [data-testid="InputInstructions"] { display: none !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.components.v1.html(
    """<script>
    var _busy = false;
    function _translateUploader() {
        if (_busy) return;
        _busy = true;
        try {
            var doc = window.parent ? window.parent.document : document;
            var zones = doc.querySelectorAll('[data-testid="stFileUploaderDropzone"]');
            zones.forEach(function(zone) {
                zone.querySelectorAll('span, p, small, div, button').forEach(function(el) {
                    if (el.childElementCount === 0) {
                        var t = el.textContent;
                        if (t.indexOf('Drag and drop') >= 0 ||
                            t.indexOf('Limit') >= 0 ||
                            t.indexOf('Browse files') >= 0) {
                            el.textContent = t
                                .replace('Drag and drop file here', 'Glissez-déposez votre fichier ici')
                                .replace('Drag and drop files here', 'Glissez-déposez vos fichiers ici')
                                .replace(/Limit \\d+MB per file/, 'Taille max : 20 Mo')
                                .replace('Limit 200MB per file', 'Taille max : 20 Mo')
                                .replace('Browse files', 'Parcourir');
                        }
                    }
                });
            });
        } catch(e) {}
        _busy = false;
    }
    _translateUploader();
    var _obs = new MutationObserver(_translateUploader);
    try {
        _obs.observe(window.parent ? window.parent.document.body : document.body,
            { childList: true, subtree: true });
    } catch(e) {}
    </script>""",
    height=0,
)

# Header
st.markdown(
    """<div style="text-align: center; padding: 20px 0;">
        <h2>Nouvelle Analyse ESG</h2>
        <p style="color: #6B7280;">Uploadez un rapport de durabilité pour obtenir votre analyse en quelques minutes.</p>
    </div>""",
    unsafe_allow_html=True,
)

# Rapport échantillon (si venu de l'onboarding)
if st.session_state.get("use_sample_report"):
    st.info(
        "Mode démonstration : un rapport d'exemple sera utilisé. "
        "Vous pouvez aussi uploader votre propre rapport ci-dessous."
    )
    st.session_state.pop("use_sample_report", None)

# Formulaire d'upload
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
    # FIX #3 : année par défaut = année N-1 (les rapports ESG couvrent l'exercice précédent)
    import datetime as _dt
    _default_year = _dt.datetime.now().year - 1  # 2025 en 2026
    report_year = st.number_input(
        "Année du rapport",
        min_value=2000,
        max_value=_dt.datetime.now().year + 1,
        value=_default_year,
        step=1,
        help=f"Année de l'exercice couvert par le rapport (généralement {_default_year}).",
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
    format_func=lambda x: "- Sélectionner un secteur -" if x is None else x,
)

# Bouton Analyser
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
        track_upload_started(company_name.strip(), sector)  # Event #3 funnel

        st.success(f"Analyse #{analysis_id} lancée !")

        # 2. Polling avec indicateur de progression 4 étapes
        status_container = st.empty()
        progress_bar = st.progress(0)

        # Étapes visuelles de l'analyse
        ANALYSIS_STEPS = [
            (0, 15, "Extraction du texte du document..."),
            (15, 40, "Identification des indicateurs ESG..."),
            (40, 75, "Évaluation de la couverture ESRS..."),
            (75, 95, "Calcul des scores et recommandations..."),
        ]

        # Indicateur visuel des étapes
        step_display = st.empty()

        def _render_steps(current_step_idx: int):
            """Affiche les 4 étapes avec indicateur visuel."""
            html_parts = []
            labels = ["Extraction", "Identification", "Évaluation ESRS", "Scoring"]
            for i, label in enumerate(labels):
                if i < current_step_idx:
                    color, icon = "#1A3D22", "&#10003;"
                elif i == current_step_idx:
                    color, icon = "#1A3D22", "&#9679;"
                else:
                    color, icon = "#D1D5DB", "&#9675;"
                html_parts.append(
                    f'<div style="display:flex; align-items:center; gap:8px; margin:4px 0;">'
                    f'<span style="color:{color}; font-size:14px;">{icon}</span>'
                    f'<span style="color:{"#1A3D22" if i <= current_step_idx else "#9CA3AF"}; '
                    f'font-size:13px; {"font-weight:600;" if i == current_step_idx else ""}">{label}</span>'
                    f'</div>'
                )
            step_display.markdown("".join(html_parts), unsafe_allow_html=True)

        poll_count = 0
        max_polls = 60

        while poll_count < max_polls:
            time.sleep(3)
            poll_count += 1

            try:
                analysis = get_analysis(token, analysis_id)
            except APIError:
                continue

            current_status = analysis.get("status", "pending")

            if current_status == "pending":
                progress_bar.progress(5, text="En attente de traitement...")
                _render_steps(0)
            elif current_status == "processing":
                # Simuler la progression à travers les 4 étapes
                step_idx = min(poll_count // 5, 3)
                lo, hi, label = ANALYSIS_STEPS[step_idx]
                frac = (poll_count % 5) / 5
                pct = int(lo + (hi - lo) * frac)
                pct = min(pct, 95)
                progress_bar.progress(pct, text=label)
                _render_steps(step_idx)
            elif current_status == "success":
                progress_bar.progress(100, text="Analyse terminée !")
                _render_steps(4)
                status_container.success("Analyse terminée avec succès !")
                # Event #4 funnel - score récupéré depuis la réponse API
                _user_plan = get_user().get("plan") if get_user() else None
                track_analysis_completed(
                    score=analysis.get("score_global"),
                    plan=_user_plan,
                )
                time.sleep(1.5)
                # FIX #4 : redirection directe vers Résultats sans rerun intermédiaire
                st.switch_page("pages/3_Resultats.py")
            elif current_status == "failed":
                progress_bar.empty()
                step_display.empty()
                error_msg = analysis.get("error_message", "Erreur inconnue")
                status_container.error(f"L'analyse a échoué : {error_msg}")
                break

        else:
            progress_bar.empty()
            step_display.empty()
            status_container.warning(
                "L'analyse prend plus de temps que prévu. "
                "Vérifiez les résultats dans quelques minutes via le Dashboard."
            )

    except APIError as e:
        import json as _json
        # Extraire le message lisible depuis une réponse JSON brute
        try:
            _raw = _json.loads(e.detail) if isinstance(e.detail, str) else e.detail
            _msg = _raw.get("error", str(e.detail)) if isinstance(_raw, dict) else str(e.detail)
        except Exception:
            _msg = str(e.detail)

        if e.status_code == 403:
            # Plan insuffisant -> proposer upgrade
            st.markdown(
                '<div style="background:#FFF7ED;border:1.5px solid #FB923C;border-radius:12px;'
                'padding:20px;text-align:center;margin:8px 0;">'
                '<div style="font-size:22px;margin-bottom:8px;">🔒</div>'
                '<div style="font-weight:700;color:#9A3412;font-size:15px;">'
                'Limite de votre plan atteinte</div>'
                '<div style="font-size:13px;color:#6B7280;margin-top:6px;">'
                'Vous avez utilisé votre analyse gratuite. Passez au plan '
                '<strong>Essentiel (39€/analyse)</strong> ou '
                '<strong>Pro (129€/mois illimité)</strong> pour continuer.'
                '</div></div>',
                unsafe_allow_html=True,
            )
            if st.button("🚀 Voir les tarifs et continuer", type="primary",
                         use_container_width=True, key="upload_upgrade"):
                st.switch_page("pages/6_Tarifs.py")
        elif e.status_code == 429:
            st.warning("Trop de requêtes - merci de patienter quelques instants avant de réessayer.")
        elif e.status_code and e.status_code >= 500:
            st.error("Le service est temporairement indisponible. Merci de réessayer dans quelques minutes.")
        else:
            st.error(f"Une erreur est survenue : {_msg}")
    except Exception:
        st.error("Impossible de contacter le serveur. Vérifiez votre connexion réseau et réessayez.")

# Bandeau quota restant (plan discovery)
_upload_user = get_user()
if _upload_user:
    _upload_plan = _upload_user.get("plan", "discovery")
    _analyses_count = _upload_user.get("analyses_this_month", 0)
    if _upload_plan in ("discovery", "free"):
        remaining = max(0, 1 - _analyses_count)
        if remaining == 0:
            st.info("Vous avez utilisé votre analyse gratuite. Passez à un plan payant pour continuer.")
        else:
            st.caption(f"Plan Découverte - {remaining} analyse gratuite restante.")

# Aide
if not can_submit:
    st.caption("Uploadez un fichier et renseignez le nom de l'entreprise pour lancer l'analyse.")

with st.expander("Comment ça marche ?"):
    st.markdown(
        """1. **Upload** - Déposez votre rapport de durabilité (PDF, Word ou Excel)
2. **Extraction** - Le texte est extrait automatiquement du document
3. **Analyse IA** - GPT-4o analyse le contenu selon les standards ESRS/CSRD
4. **Résultats** - Scores E/S/G, conformité CSRD, KPIs détectés, recommandations
5. **Rapport PDF** - Téléchargez un rapport professionnel prêt à partager"""
    )
