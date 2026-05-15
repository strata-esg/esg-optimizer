"""
ESG Optimizer MVP - Landing page publique.
Première page Streamlit (préfixe 0_) - accessible sans connexion.
Contient : Hero, cards persona, preuve sociale, démo, comment ça marche,
pricing 4 plans, FAQ, footer.
"""

import streamlit as st
import sys
from pathlib import Path

# Path setup
_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from frontend.components.analytics import (
    track_landing_view,
    track_pricing_viewed,
    track_quick_check_submit,
    track_quick_check_completed,
    track_cta_landing_click,
    track_payment_completed,
)
from frontend.utils.session import is_logged_in, get_token, save_user
from frontend.utils.api_client import quick_check_upload, quick_check_result, APIError, get_me
from frontend.utils.styles import inject_global_styles

# Juste après st.set_page_config(...)
from frontend.components.seo import seo_for
seo_for("landing")
inject_global_styles()

# Query params
params = st.query_params
persona = params.get("persona", None)

# -- Détection paiement complété (redirect Stripe) -----------------------------
# Stripe Payment Link doit être configuré avec :
#   success_url = https://<app-url>/?payment_success=1&plan=essential  (ou pro)
_payment_success = params.get("payment_success", None)
_payment_plan    = params.get("plan", None)
if _payment_success == "1" and _payment_plan in ("essential", "pro"):
    track_payment_completed(_payment_plan)
    st.toast(f"🎉 Paiement confirmé - bienvenue sur le plan {_payment_plan.title()} !", icon="✅")
    # Rafraîchir les données utilisateur pour mettre à jour la sidebar
    _tok = get_token()
    if _tok:
        try:
            _fresh_user = get_me(_tok)
            save_user(_fresh_user)
        except Exception:
            pass

track_landing_view(persona)

# Contenu personnalisé par persona
PERSONA_CONTENT = {
    "pme": {
        "titre": "PME : Votre rapport CSRD est-il conforme ?",
        "sous_titre": "Pas besoin d'un cabinet à 15 000 €. En 3 minutes, notre IA analyse votre rapport de durabilité et vous dit exactement ce qui manque.",
        "cta": "Vérifier mon rapport gratuitement",
        "argument": "Idéal pour les PME qui font 1 à 2 rapports par an. Payez à l'analyse, pas au mois.",
    },
    "consultant": {
        "titre": "Consultants : Automatisez vos analyses ESG",
        "sous_titre": "Passez de 2 jours à 3 minutes par rapport client. White-label, export Excel, analyses illimitées.",
        "cta": "Tester gratuitement sur un rapport client",
        "argument": "Le plan Pro vous fait gagner 80% de temps sur vos livrables ESG. Vos clients ne voient que votre marque.",
    },
    "drse": {
        "titre": "Directeurs RSE : Pilotez votre conformité CSRD",
        "sous_titre": "Benchmark sectoriel, suivi pluriannuel, Delta Report pour justifier votre budget en COMEX.",
        "cta": "Analyser mon rapport 2025",
        "argument": "Comparez vos scores aux entreprises de votre secteur. Montrez votre progression année après année.",
    },
    "enterprise": {
        "titre": "Entreprises : Conformité CSRD sécurisée à grande échelle",
        "sous_titre": "SSO, multi-utilisateurs, API, hébergement dédié. Une solution conforme RGPD pour vos équipes.",
        "cta": "Demander une démo personnalisée",
        "argument": "Onboarding dédié, SLA garanti, DPA signé. Vos données restent en Europe.",
    },
}

# Contenu par défaut (générique)
default_content = {
    "titre": "Votre rapport CSRD analysé en 3 minutes.",
    "sous_titre": "Obtenez votre score ESG en 3 minutes. Notre agent analyse votre rapport de durabilité et génère un diagnostic complet : scores E/S/G, conformité ESRS, recommandations priorisées.",
    "cta": "Analyser mon rapport gratuitement",
    "argument": "Déjà utilisé par des PME, consultants ESG et directeurs RSE pour préparer leur conformité CSRD.",
}

content = PERSONA_CONTENT.get(persona, default_content) if persona else default_content

# Bouton secondaire du HERO :
#   - quand AUCUN persona : "Je suis consultant ->" (lien vers ?persona=consultant)
#   - quand un persona est déjà actif : "← Retour à la version générale"
#   Ça évite la boucle "je clique sur Je suis consultant -> ça ouvre la même page".
if persona:
    _hero_secondary_cta = (
        '<a href="?" style="display:inline-block;background:transparent;'
        'color:#1B3D20;font-family:\'DM Sans\',sans-serif;font-size:14px;font-weight:500;'
        'padding:14px 24px;border-radius:10px;text-decoration:none;'
        'border:1.5px solid #1B3D20;">&#8592; Retour à la version générale</a>'
    )
else:
    _hero_secondary_cta = (
        '<a href="?persona=consultant" style="display:inline-block;background:transparent;'
        'color:#1B3D20;font-family:\'DM Sans\',sans-serif;font-size:14px;font-weight:500;'
        'padding:14px 24px;border-radius:10px;text-decoration:none;'
        'border:1.5px solid #1B3D20;">Je suis consultant &#8594;</a>'
    )


# 1. HERO - Logo + CTA proéminent above the fold
st.markdown(
    f"""<div style="text-align: center; padding: 40px 20px 10px 20px;">
        <div style="margin-bottom: 18px;">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 56 56"
                 fill="none" width="64" height="64" style="display:inline-block;">
                <circle cx="28" cy="28" r="27" fill="#1B3D20" stroke="none"/>
                <path d="M 10,34 A 18,18 0 1,1 46,34"
                    stroke="rgba(212,240,216,0.25)" stroke-width="4"
                    stroke-linecap="round" fill="none"/>
                <path d="M 10,34 A 18,18 0 0,1 38,12"
                    stroke="#7FC686" stroke-width="4"
                    stroke-linecap="round" fill="none"/>
                <circle cx="28" cy="31" r="3" fill="#D4F0D8"/>
                <line x1="28" y1="31" x2="40" y2="16"
                    stroke="#D4F0D8" stroke-width="2.2" stroke-linecap="round"/>
                <circle cx="40" cy="16" r="2.5" fill="#7FC686"/>
            </svg>
        </div>
        <h1 style="margin-top:0; color:#1B3D20; font-size:2.6rem; line-height:1.15;
            font-family:'DM Serif Display',Georgia,serif; font-weight:400;">
            {content['titre']}
        </h1>
        <p style="font-size:17px; color:#6B7280; max-width:620px; margin:14px auto 28px auto;
            line-height:1.65;">
            {content['sous_titre']}
        </p>
        <div style="display:flex; justify-content:center; gap:12px; flex-wrap:wrap; margin-bottom:8px;">
            <a href="#quick-check" style="display:inline-block; background:#1B3D20; color:#D4F0D8;
                font-family:'DM Sans',sans-serif; font-size:15px; font-weight:600;
                padding:14px 32px; border-radius:10px; text-decoration:none;
                box-shadow:0 4px 14px rgba(27,61,32,0.3);"
                onmouseover="this.style.background='#2A5C34'"
                onmouseout="this.style.background='#1B3D20'">
                &#9654;&nbsp; Analyser gratuitement · 3 min
            </a>
            {_hero_secondary_cta}
        </div>
        <div style="font-size:12px; color:#9CA3AF; margin-top:8px;">
            Aucun compte requis &nbsp;&#183;&nbsp; PDF, DOCX ou XLSX &nbsp;&#183;&nbsp; Résultat en ~3 minutes
        </div>
    </div>""",
    unsafe_allow_html=True,
)

# -- QUICK-CHECK PUBLIC - Redesign avec design tokens ------------------------
st.markdown(
    """
    <style>
    /* File uploader zone - dashed green */
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
    /* Score DM Serif */
    .qc-score-num {
        font-family: 'DM Serif Display', Georgia, serif !important;
        font-weight: 400 !important;
        letter-spacing: -0.04em !important;
        line-height: 1 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Ancre HTML pour le scroll depuis le CTA hero
st.markdown('<div id="quick-check" style="height:0;margin:0;padding:0;"></div>', unsafe_allow_html=True)

# JS : traduit les textes anglais de Streamlit - flag anti-boucle infinie
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
                zone.querySelectorAll('span, p, small, div').forEach(function(el) {
                    if (el.childElementCount === 0) {
                        var t = el.textContent;
                        if (t.indexOf('Drag and drop') >= 0 ||
                            t.indexOf('Limit 200MB') >= 0 ||
                            t.indexOf('Browse files') >= 0) {
                            el.textContent = t
                                .replace('Drag and drop file here', 'Glissez-deposez votre fichier ici')
                                .replace('Limit 200MB per file', 'Taille max : 200 Mo')
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

# Header de la section
_, _qh, _ = st.columns([1, 4, 1])
with _qh:
    st.markdown(
        """
        <div style="background:#F7F2E8; border:1.5px solid #1B3D20; border-radius:18px;
            padding:28px 36px 16px; margin:4px 0 0 0; text-align:center;">
            <div style="font-family:'DM Serif Display',Georgia,serif; font-size:1.6rem;
                color:#1B3D20; letter-spacing:-0.02em; margin-bottom:6px;">
                Analysez votre rapport ESG - gratuit
            </div>
            <div style="font-family:'DM Sans',sans-serif; font-size:13px; color:#6B7280;">
                Aucun compte requis &nbsp;·&nbsp; PDF, DOCX ou XLSX &nbsp;·&nbsp; Résultat en ~3 minutes
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Upload widget centré
qc_col_l, qc_col_center, qc_col_r = st.columns([1, 3, 1])
with qc_col_center:
    uploaded_file = st.file_uploader(
        "Glissez ou sélectionnez votre rapport de durabilité",
        type=["pdf", "docx", "xlsx"],
        help="PDF, DOCX ou XLSX - 10 Mo max. Aucun compte requis.",
        key="quick_check_uploader",
        label_visibility="collapsed",
    )

    if uploaded_file is not None and "qc_token" not in st.session_state:
        track_quick_check_submit(uploaded_file.name)  # Event #2 funnel
        with st.spinner("Analyse en cours... (~30 secondes)"):
            try:
                file_bytes = uploaded_file.read()
                result = quick_check_upload(file_bytes, uploaded_file.name)
                st.session_state["qc_token"] = result["token"]
            except APIError as e:
                if e.status_code == 429:
                    st.warning(e.detail)
                else:
                    st.error(f"Erreur : {e.detail}")
            except Exception as e:
                st.error(f"Erreur de connexion au serveur : {e}")

    # Polling du résultat
    if "qc_token" in st.session_state:
        import time as _time

        token = st.session_state["qc_token"]
        max_polls = 40  # 40 × 3s = 2 minutes max

        if "qc_result" not in st.session_state:
            progress_bar = st.progress(0, text="Extraction du texte...")
            for i in range(max_polls):
                try:
                    qc = quick_check_result(token)
                except Exception:
                    _time.sleep(3)
                    continue

                if qc["status"] == "success":
                    st.session_state["qc_result"] = qc
                    progress_bar.progress(100, text="Analyse terminée !")
                    track_quick_check_completed(qc.get("score_global"))
                    break
                elif qc["status"] == "failed":
                    progress_bar.empty()
                    st.error(f"L'analyse a échoué : {qc.get('error_message', 'Erreur inconnue')}")
                    break
                else:
                    pct = min(int((i / max_polls) * 95), 95)
                    steps = ["Extraction du texte...", "Analyse IA en cours...",
                             "Scoring ESRS...", "Finalisation..."]
                    step = steps[min(i // 10, 3)]
                    progress_bar.progress(pct, text=step)
                    _time.sleep(3)

        # -- Résultat ----------------------------------------------------------
        if "qc_result" in st.session_state:
            qc = st.session_state["qc_result"]
            score = qc.get("score_global", 0)
            csrd = qc.get("csrd_ready", False)
            strengths = qc.get("teaser_strengths", [])
            weaknesses = qc.get("teaser_weaknesses", [])

            # Couleurs score
            if score >= 70:
                _sc, _sb = "#1B3D20", "#D4F0D8"
            elif score >= 40:
                _sc, _sb = "#D97706", "#FEF3C7"
            else:
                _sc, _sb = "#DC2626", "#FEE2E2"

            # Badge CSRD 4 niveaux
            _csrd_pct = qc.get("csrd_coverage_pct")  # présent si le backend le renvoie
            if _csrd_pct is not None:
                if _csrd_pct >= 100:
                    _bl, _bs = "CSRD Ready ✓", "background:#D4F0D8;color:#1B3D20;"
                elif _csrd_pct >= 80:
                    _bl, _bs = "Conformité Avancée", "background:#DBEAFE;color:#1E40AF;"
                elif _csrd_pct >= 50:
                    _bl, _bs = "En cours de structuration", "background:#FFF7ED;color:#9A3412;"
                else:
                    _bl, _bs = "Lacunes majeures", "background:#FEE2E2;color:#991B1B;"
            else:
                # Approximation : csrd_ready + score
                if csrd:
                    _bl, _bs = "CSRD Ready ✓", "background:#D4F0D8;color:#1B3D20;"
                elif score >= 60:
                    _bl, _bs = "En cours de structuration", "background:#FFF7ED;color:#9A3412;"
                else:
                    _bl, _bs = "Lacunes majeures", "background:#FEE2E2;color:#991B1B;"

            csrd_badge_html = (
                f'<span style="{_bs}padding:5px 14px;border-radius:20px;'
                f'font-family:\'DM Sans\',sans-serif;font-size:13px;'
                f'font-weight:600;letter-spacing:0.01em;">{_bl}</span>'
            )

            # Score card principal
            st.markdown(
                f"""
                <div style="background:#FFFFFF; border:1.5px solid {_sc}; border-radius:16px;
                    padding:28px 20px 20px; margin:18px 0 12px; text-align:center;
                    box-shadow:0 2px 12px rgba(0,0,0,0.06);">
                    <div style="font-family:'DM Sans',sans-serif; font-size:11px;
                        color:#6B7280; text-transform:uppercase; letter-spacing:0.08em;
                        margin-bottom:8px;">Score global ESG</div>
                    <div class="qc-score-num" style="font-size:5rem; color:{_sc};">
                        {score}
                        <span style="font-family:'DM Sans',sans-serif; font-size:1.2rem;
                            color:#9CA3AF; font-weight:400;">/100</span>
                    </div>
                    <div style="margin-top:12px;">{csrd_badge_html}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Forces et lacunes avec flou partiel
            force_col, weak_col = st.columns(2)
            with force_col:
                st.markdown(
                    '<div style="font-family:\'DM Sans\',sans-serif; font-size:13px; '
                    'font-weight:600; color:#1B3D20; margin-bottom:8px;">✦ Forces détectées</div>',
                    unsafe_allow_html=True,
                )
                for i, s in enumerate(strengths):
                    if i == 0:
                        st.markdown(
                            f'<div style="font-family:\'DM Sans\',sans-serif; font-size:13px; '
                            f'color:#374151; margin-bottom:6px; padding:8px 10px; '
                            f'background:#F0FAF0; border-radius:8px;">· {s}</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f'<div style="filter:blur(4px); user-select:none; '
                            f'font-family:\'DM Sans\',sans-serif; font-size:13px; '
                            f'color:#6B7280; margin-bottom:6px; padding:8px 10px; '
                            f'background:#F9FAFB; border-radius:8px;">· {s}</div>',
                            unsafe_allow_html=True,
                        )

            with weak_col:
                st.markdown(
                    '<div style="font-family:\'DM Sans\',sans-serif; font-size:13px; '
                    'font-weight:600; color:#DC2626; margin-bottom:8px;">✦ Lacunes détectées</div>',
                    unsafe_allow_html=True,
                )
                for i, w in enumerate(weaknesses):
                    if i == 0:
                        st.markdown(
                            f'<div style="font-family:\'DM Sans\',sans-serif; font-size:13px; '
                            f'color:#374151; margin-bottom:6px; padding:8px 10px; '
                            f'background:#FEF2F2; border-radius:8px;">· {w}</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f'<div style="filter:blur(4px); user-select:none; '
                            f'font-family:\'DM Sans\',sans-serif; font-size:13px; '
                            f'color:#6B7280; margin-bottom:6px; padding:8px 10px; '
                            f'background:#F9FAFB; border-radius:8px;">· {w}</div>',
                            unsafe_allow_html=True,
                        )

            # CTA upgrade
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            st.markdown(
                """
                <div style="background:#1B3D20; border-radius:12px; padding:20px 24px;
                    text-align:center;">
                    <div style="font-family:'DM Serif Display',Georgia,serif; font-size:1.1rem;
                        color:#FFFFFF; margin-bottom:4px;">
                        Débloquez le rapport complet
                    </div>
                    <div style="font-family:'DM Sans',sans-serif; font-size:12.5px;
                        color:rgba(255,255,255,0.65);">
                        10 standards ESRS · Recommandations priorisées · PDF 8 pages
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.page_link(
                "pages/1_Login.py",
                label="Créer un compte gratuit - 30 secondes",
                use_container_width=True,
            )

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if st.button("↩ Analyser un autre rapport", use_container_width=True):
                del st.session_state["qc_token"]
                del st.session_state["qc_result"]
                st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# 2. CARDS PERSONA "Je suis..."
if not persona:  # N'afficher que sur la landing générique
    st.markdown(
        """<div style="text-align: center; margin-bottom: 8px;">
            <span style="font-size: 14px; color: #9CA3AF; text-transform: uppercase; letter-spacing: 1px;">
                Je suis...
            </span>
        </div>""",
        unsafe_allow_html=True,
    )

    p1, p2, p3, p4 = st.columns(4)

    # SVG icons inline (Lucide-style, 28px, brand color)
    _ico = lambda d: f'<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#1A3D22" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{d}</svg>'
    _ico_building = _ico('<rect x="4" y="2" width="16" height="20" rx="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01M16 6h.01M12 6h.01M8 10h.01M16 10h.01M12 10h.01M8 14h.01M16 14h.01M12 14h.01"/>')
    _ico_clipboard = _ico('<rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M12 11h4M12 16h4M8 11h.01M8 16h.01"/>')
    _ico_target = _ico('<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>')
    _ico_landmark = _ico('<line x1="3" y1="22" x2="21" y2="22"/><line x1="6" y1="18" x2="6" y2="11"/><line x1="10" y1="18" x2="10" y2="11"/><line x1="14" y1="18" x2="14" y2="11"/><line x1="18" y1="18" x2="18" y2="11"/><polygon points="12 2 20 7 4 7"/>')

    persona_cards = [
        (p1, _ico_building, "PME / ETI", "Préparer ma conformité CSRD", "pme"),
        (p2, _ico_clipboard, "Consultant ESG", "Gagner du temps sur mes livrables", "consultant"),
        (p3, _ico_target, "Directeur RSE", "Piloter ma performance ESG", "drse"),
        (p4, _ico_landmark, "Entreprise", "Déployer à grande échelle", "enterprise"),
    ]

    for col, icon, title, desc, key in persona_cards:
        with col:
            st.markdown(
                f"""<a href="?persona={key}" style="text-decoration: none; display: block;">
                    <div style="background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 12px;
                        padding: 20px 16px; text-align: center; min-height: 140px; cursor: pointer;
                        transition: border-color 0.2s, box-shadow 0.2s;"
                        onmouseover="this.style.borderColor='#1A3D22'; this.style.boxShadow='0 2px 8px rgba(26,61,34,0.15)';"
                        onmouseout="this.style.borderColor='#E5E7EB'; this.style.boxShadow='none';">
                        <div>{icon}</div>
                        <div style="font-weight: 600; font-size: 14px; margin-top: 8px; color: #111827;">
                            {title}
                        </div>
                        <div style="font-size: 12px; color: #6B7280; margin-top: 4px;">
                            {desc}
                        </div>
                        <div style="font-size: 12px; color: #1A3D22; margin-top: 8px; font-weight: 600;">
                            En savoir plus ->
                        </div>
                    </div>
                </a>""",
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

st.divider()

# 3. PREUVE SOCIALE - facts produit fixes
st.markdown(
    """<div style="text-align: center; padding: 20px 0;">
        <div style="display: flex; justify-content: center; gap: 40px; flex-wrap: wrap;">
            <div>
                <div style="font-size: 28px; font-weight: 700; color: #1A3D22;">10</div>
                <div style="font-size: 13px; color: #6B7280;">ESRS couverts</div>
            </div>
            <div>
                <div style="font-size: 28px; font-weight: 700; color: #1A3D22;">3</div>
                <div style="font-size: 13px; color: #6B7280;">Formats acceptés</div>
            </div>
            <div>
                <div style="font-size: 28px; font-weight: 700; color: #1A3D22;">3 min</div>
                <div style="font-size: 13px; color: #6B7280;">Temps d'analyse</div>
            </div>
            <div>
                <div style="font-size: 28px; font-weight: 700; color: #1A3D22;">0</div>
                <div style="font-size: 13px; color: #6B7280;">Compte requis</div>
            </div>
        </div>
        <div style="font-size: 12px; color: #9CA3AF; margin-top: 12px;">
            PDF · DOCX · XLSX &nbsp;·&nbsp; Résultats immédiats · Aucun engagement
        </div>
    </div>""",
    unsafe_allow_html=True,
)

st.divider()

# 4. COMMENT ÇA MARCHE - 3 étapes
st.markdown(
    """<div style="text-align: center; padding: 10px 0 20px 0;">
        <h2 style="color: #111827;">Comment ça marche</h2>
        <p style="color: #6B7280; font-size: 15px;">Un diagnostic ESG complet en 3 étapes simples</p>
    </div>""",
    unsafe_allow_html=True,
)

s1, s2, s3 = st.columns(3)

_s = lambda d: f'<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#1A3D22" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{d}</svg>'
_step_upload = _s('<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>')
_step_cpu = _s('<rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M15 2v2M15 20v2M2 15h2M2 9h2M20 15h2M20 9h2M9 2v2M9 20v2"/>')
_step_chart = _s('<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>')

steps = [
    (s1, "1", _step_upload, "Uploadez votre rapport",
     "Glissez votre rapport de durabilité (PDF, DOCX ou XLSX). DPEF, rapport RSE, bilan carbone - tout fonctionne."),
    (s2, "2", _step_cpu, "L'IA analyse en 3 minutes",
     "GPT-4o parcourt votre document, identifie les KPIs, évalue la couverture ESRS et calcule vos scores E/S/G."),
    (s3, "3", _step_chart, "Recevez votre diagnostic",
     "Score global, conformité CSRD, forces/lacunes, recommandations priorisées et rapport PDF téléchargeable."),
]

for col, num, icon, title, desc in steps:
    with col:
        st.markdown(
            f"""<div style="background: linear-gradient(135deg, #F0FDF4 0%, #ECFDF5 100%);
                border-radius: 12px; padding: 28px 20px; text-align: center; min-height: 220px;">
                <div style="background: #1A3D22; color: white; width: 32px; height: 32px;
                    border-radius: 50%; display: inline-flex; align-items: center; justify-content: center;
                    font-weight: 700; font-size: 14px; margin-bottom: 12px;">{num}</div>
                <div style="margin-bottom: 8px;">{icon}</div>
                <div style="font-weight: 600; font-size: 15px; color: #111827; margin-bottom: 6px;">
                    {title}
                </div>
                <div style="font-size: 13px; color: #6B7280; line-height: 1.5;">
                    {desc}
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)
st.divider()

# 5. DÉMO VISUELLE - Aperçu des résultats
st.markdown(
    """<div style="text-align: center; padding: 10px 0 20px 0;">
        <h2 style="color: #111827;">Ce que vous obtenez</h2>
        <p style="color: #6B7280; font-size: 15px;">Un rapport complet avec des recommandations actionnables</p>
    </div>""",
    unsafe_allow_html=True,
)

demo_l, demo_r = st.columns(2)

with demo_l:
    st.markdown(
        """<div style="background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 12px; padding: 24px;">
            <div style="font-weight: 600; font-size: 15px; color: #111827; margin-bottom: 12px;">
                Scores ESG détaillés
            </div>
            <div style="display: flex; gap: 12px; margin-bottom: 16px;">
                <div style="flex: 1; background: #D4F0D8; border-radius: 8px; padding: 12px; text-align: center;">
                    <div style="font-size: 24px; font-weight: 700; color: #1A3D22;">72</div>
                    <div style="font-size: 11px; color: #6B7280;">Environnement</div>
                </div>
                <div style="flex: 1; background: #DBEAFE; border-radius: 8px; padding: 12px; text-align: center;">
                    <div style="font-size: 24px; font-weight: 700; color: #2563EB;">65</div>
                    <div style="font-size: 11px; color: #6B7280;">Social</div>
                </div>
                <div style="flex: 1; background: #EDE9FE; border-radius: 8px; padding: 12px; text-align: center;">
                    <div style="font-size: 24px; font-weight: 700; color: #7C3AED;">58</div>
                    <div style="font-size: 11px; color: #6B7280;">Gouvernance</div>
                </div>
            </div>
            <div style="background: white; border-radius: 8px; padding: 12px; border: 1px solid #E5E7EB;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 13px; color: #6B7280;">Score global</span>
                    <span style="font-size: 20px; font-weight: 700; color: #1A3D22;">65/100</span>
                </div>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

with demo_r:
    st.markdown(
        """<div style="background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 12px; padding: 24px;">
            <div style="font-weight: 600; font-size: 15px; color: #111827; margin-bottom: 12px;">
                Conformité CSRD
            </div>
            <div style="background: #FEF3C7; border-radius: 8px; padding: 12px; margin-bottom: 12px;">
                <div style="font-size: 13px; color: #92400E;">
                    <strong>Partiellement conforme</strong> · Couverture ESRS : 68%
                </div>
            </div>
            <div style="font-size: 13px; color: #374151; margin-bottom: 8px; font-weight: 600;">
                Standards à renforcer :
            </div>
            <div style="font-size: 12px; color: #6B7280; line-height: 1.8;">
                <span style="color:#EF4444;">&#10007;</span> E1 - Changement climatique<br>
                <span style="color:#EF4444;">&#10007;</span> S2 - Travailleurs de la chaîne de valeur<br>
                <span style="color:#F59E0B;">&#9679;</span> G1 - Gouvernance (partiel)<br>
                <span style="color:#1A3D22;">&#10003;</span> E3 - Eau et ressources marines<br>
                <span style="color:#1A3D22;">&#10003;</span> S1 - Effectifs de l'entreprise
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# Ligne de features complémentaires
f1, f2, f3, f4 = st.columns(4)
_fi = lambda d: f'<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#1A3D22" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{d}</svg>'
features_extra = [
    (f1, _fi('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>'), "Rapport PDF", "8 pages téléchargeables"),
    (f2, _fi('<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>'), "Delta Report", "Évolution année par année"),
    (f3, _fi('<line x1="9" y1="18" x2="15" y2="18"/><line x1="10" y1="22" x2="14" y2="22"/><path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"/>'), "Recommandations", "Priorisées par impact"),
    (f4, _fi('<path d="M6 9H4.5a2.5 2.5 0 0 1 0-5C7 4 9 7 12 7s5-3 7.5-3a2.5 2.5 0 0 1 0 5H18"/><path d="M18 22H6"/><path d="M6 13v-2"/><path d="M18 13v-2"/><path d="M6 17v-2"/><path d="M18 17v-2"/>'), "Benchmark", "Comparaison sectorielle"),
]
for col, icon, title, desc in features_extra:
    with col:
        st.markdown(
            f"""<div style="text-align: center; padding: 16px 8px;">
                <div>{icon}</div>
                <div style="font-weight: 600; font-size: 13px; color: #111827; margin-top: 4px;">{title}</div>
                <div style="font-size: 11px; color: #9CA3AF;">{desc}</div>
            </div>""",
            unsafe_allow_html=True,
        )

st.divider()

# 6. PRICING - 4 plans
track_pricing_viewed(persona)

st.markdown(
    """<div style="text-align: center; padding: 10px 0 20px 0;">
        <h2 style="color: #111827;">Tarifs simples, sans engagement</h2>
        <p style="color: #6B7280; font-size: 15px;">Commencez gratuitement. Passez au supérieur quand vous êtes prêt.</p>
    </div>""",
    unsafe_allow_html=True,
)

pr1, pr2, pr3, pr4 = st.columns(4)

# Plan Découverte
with pr1:
    st.markdown(
        """<div style="background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 12px;
            padding: 24px 16px; text-align: center; height: 380px; overflow: visible;">
            <div style="font-weight: 700; font-size: 16px; color: #111827;">Découverte</div>
            <div style="font-size: 32px; font-weight: 800; color: #1A3D22; margin: 12px 0 4px 0;">0 €</div>
            <div style="font-size: 12px; color: #9CA3AF; margin-bottom: 16px;">1 analyse gratuite</div>
            <div style="text-align: left; font-size: 12px; color: #6B7280; line-height: 2;">
                <span style="color:#1A3D22;">&#10003;</span> 1 analyse complète<br>
                <span style="color:#1A3D22;">&#10003;</span> Score global E/S/G<br>
                <span style="color:#6B7280;">&#9679;</span> Rapport PDF (3 pages, watermark)<br>
                <span style="color:#B53030;">&#10007;</span> Pas de Delta Report<br>
                <span style="color:#B53030;">&#10007;</span> Pas de scores détaillés<br>
                <span style="color:#B53030;">&#10007;</span> Historique limité à 1 analyse
            </div>
        </div>""",
        unsafe_allow_html=True,
    )
    if st.button("Commencer gratuitement", key="cta_discovery", use_container_width=True):
        track_cta_landing_click("Commencer gratuitement", source="pricing_discovery")
        st.switch_page("pages/1_Login.py")

# Plan Essentiel
with pr2:
    st.markdown(
        """<div style="background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 12px;
            padding: 24px 16px; text-align: center; height: 380px; overflow: visible;">
            <div style="font-weight: 700; font-size: 16px; color: #111827;">Essentiel</div>
            <div style="font-size: 32px; font-weight: 800; color: #2563EB; margin: 12px 0 4px 0;">39 €</div>
            <div style="font-size: 12px; color: #9CA3AF; margin-bottom: 16px;">par analyse</div>
            <div style="text-align: left; font-size: 12px; color: #6B7280; line-height: 2;">
                <span style="color:#1A3D22;">&#10003;</span> Rapport complet sans watermark<br>
                <span style="color:#1A3D22;">&#10003;</span> Scores E/S/G détaillés<br>
                <span style="color:#1A3D22;">&#10003;</span> Delta Report inclus<br>
                <span style="color:#1A3D22;">&#10003;</span> Conservation 12 mois<br>
                <span style="color:#B53030;">&#10007;</span> Pas de benchmark sectoriel<br>
                <span style="color:#B53030;">&#10007;</span> Pas de white-label
            </div>
        </div>""",
        unsafe_allow_html=True,
    )
    if st.button("Commencer · 1 analyse gratuite", key="cta_essential", use_container_width=True):
        track_cta_landing_click("Acheter une analyse", source="pricing_essential")
        st.switch_page("pages/6_Tarifs.py")

# Plan Pro (RECOMMANDÉ)
with pr3:
    st.markdown(
        """<div style="background: #F0FDF4; border: 2px solid #1A3D22; border-radius: 12px;
            padding: 24px 16px; text-align: center; height: 380px; overflow: visible; position: relative;">
            <div style="position: absolute; top: -12px; left: 50%; transform: translateX(-50%);
                background: #1A3D22; color: white; padding: 2px 14px; border-radius: 10px;
                font-size: 11px; font-weight: 700;">RECOMMANDÉ</div>
            <div style="font-weight: 700; font-size: 16px; color: #111827; margin-top: 4px;">Pro</div>
            <div style="font-size: 32px; font-weight: 800; color: #1A3D22; margin: 12px 0 4px 0;">129 €</div>
            <div style="font-size: 12px; color: #9CA3AF; margin-bottom: 16px;">/ mois <span style="color:#1A3D22;">(ou 990 €/an)</span></div>
            <div style="text-align: left; font-size: 12px; color: #6B7280; line-height: 2;">
                <span style="color:#1A3D22;">&#10003;</span> Analyses illimitées<br>
                <span style="color:#1A3D22;">&#10003;</span> Dashboard complet<br>
                <span style="color:#1A3D22;">&#10003;</span> Benchmark sectoriel<br>
                <span style="color:#1A3D22;">&#10003;</span> Export Excel des KPIs<br>
                <span style="color:#1A3D22;">&#10003;</span> Rapport white-label (votre logo)<br>
                <span style="color:#1A3D22;">&#10003;</span> Historique illimité
            </div>
        </div>""",
        unsafe_allow_html=True,
    )
    if st.button("Démarrer l'essai Pro", key="cta_pro", use_container_width=True, type="primary"):
        track_cta_landing_click("Démarrer l'essai Pro", source="pricing_pro")
        st.switch_page("pages/6_Tarifs.py")

# Plan Enterprise
with pr4:
    st.markdown(
        """<div style="background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 12px;
            padding: 24px 16px; text-align: center; height: 380px; overflow: visible;">
            <div style="font-weight: 700; font-size: 16px; color: #111827;">Enterprise</div>
            <div style="font-size: 32px; font-weight: 800; color: #7C3AED; margin: 12px 0 4px 0;">Sur devis</div>
            <div style="font-size: 12px; color: #9CA3AF; margin-bottom: 16px;">adapté à votre organisation</div>
            <div style="text-align: left; font-size: 12px; color: #6B7280; line-height: 2;">
                <span style="color:#1A3D22;">&#10003;</span> Tout le plan Pro<br>
                <span style="color:#1A3D22;">&#10003;</span> SSO / SAML<br>
                <span style="color:#1A3D22;">&#10003;</span> Multi-utilisateurs<br>
                <span style="color:#1A3D22;">&#10003;</span> Accès API<br>
                <span style="color:#1A3D22;">&#10003;</span> SLA garanti<br>
                <span style="color:#1A3D22;">&#10003;</span> Formation & onboarding
            </div>
        </div>""",
        unsafe_allow_html=True,
    )
    # FIX #11 : email pro pour les demandes Enterprise
    st.link_button(
        "Nous contacter",
        "mailto:contact@esg-optimizer.fr?subject=Demande%20Enterprise%20ESG%20Optimizer",
        use_container_width=True,
    )

st.divider()

# 7. FAQ
st.markdown(
    """<div style="text-align: center; padding: 10px 0 20px 0;">
        <h2 style="color: #111827;">Questions fréquentes</h2>
    </div>""",
    unsafe_allow_html=True,
)

with st.expander("Mes données sont-elles en sécurité ?"):
    st.write(
        "Oui. Vos rapports sont traités via des serveurs européens. Les données sont chiffrées "
        "en transit (HTTPS) et au repos. Nous ne partageons jamais vos documents avec des tiers. "
        "L'API OpenAI est configurée pour ne **pas** utiliser vos données à des fins d'entraînement "
        "(header `x-openai-skip-training`)."
    )

with st.expander("Qu'est-ce que la CSRD et suis-je concerné ?"):
    st.write(
        "La Corporate Sustainability Reporting Directive (CSRD) est la directive européenne qui "
        "oblige les entreprises à publier un rapport de durabilité conforme aux standards ESRS. "
        "Depuis 2025, elle s'applique aux grandes entreprises ; en 2026, aux PME cotées. "
        "Si vous avez un doute, notre analyse gratuite vous dira immédiatement si votre rapport "
        "est conforme."
    )

with st.expander("Quelle IA est utilisée ? Est-elle fiable ?"):
    st.write(
        "Nous utilisons GPT-4o d'OpenAI, le modèle le plus performant pour l'analyse de texte. "
        "Notre système prompt est calibré sur les 10 standards ESRS (E1-E5, S1-S4, G1) et produit "
        "des scores reproductibles (température 0.2). L'IA identifie les KPIs, évalue la couverture "
        "et génère des recommandations - mais ne remplace pas un auditeur. C'est un outil d'aide "
        "à la décision."
    )

with st.expander("Quels formats de rapport acceptez-vous ?"):
    st.write(
        "PDF, DOCX et XLSX. Tous les types de rapports de durabilité fonctionnent : DPEF, rapport "
        "RSE, rapport annuel avec section ESG, bilan carbone, rapport intégré. La taille maximale "
        "est de 20 Mo."
    )

with st.expander("Le plan Découverte est-il vraiment gratuit ?"):
    st.write(
        "Oui, 100% gratuit, sans carte bancaire. Vous obtenez 1 analyse complète avec un score "
        "global et un aperçu du rapport PDF (3 pages sur 8). Pour accéder au rapport complet, "
        "aux scores détaillés et au Delta Report, passez au plan Essentiel (39 €/analyse) ou Pro."
    )

with st.expander("Qu'est-ce que le Delta Report ?"):
    st.write(
        "Le Delta Report compare votre rapport actuel avec celui de l'année précédente (même "
        "entreprise). Il montre l'évolution de chaque score, les KPIs améliorés/dégradés, "
        "et les standards ESRS gagnés ou perdus. C'est un outil puissant pour les DRSE qui "
        "doivent justifier leur progression devant le COMEX."
    )

with st.expander("Puis-je supprimer mes données ?"):
    st.write(
        "Oui. Conformément au RGPD, vous pouvez demander la suppression complète de votre compte "
        "et de toutes vos données (rapports, analyses, résultats) à tout moment. Un endpoint "
        "dédié (`DELETE /users/me`) sera disponible, ou contactez-nous par email."
    )

with st.expander("Le rapport white-label fonctionne comment ?"):
    st.write(
        "Avec le plan Pro, vous pouvez remplacer le logo ESG Optimizer par le logo de votre "
        "cabinet ou de votre entreprise sur le rapport PDF. Idéal pour les consultants qui "
        "livrent des analyses à leurs clients sous leur propre marque."
    )

st.divider()

# 8. CTA FINAL
st.markdown(
    """<div style="text-align: center; padding: 30px 20px;">
        <h2 style="color: #111827;">Prêt à analyser votre rapport ESG ?</h2>
        <p style="color: #6B7280; font-size: 15px;">
            Gratuit, sans engagement, résultat en 3 minutes.
        </p>
    </div>""",
    unsafe_allow_html=True,
)

col_l2, col_cta2, col_r2 = st.columns([1, 2, 1])
with col_cta2:
    if is_logged_in():
        if st.button("Lancer mon analyse gratuite", key="cta_final_logged", use_container_width=True, type="primary"):
            track_cta_landing_click("Lancer mon analyse gratuite", source="footer_cta")
            st.switch_page("pages/2_Upload.py")
    else:
        if st.button("Créer mon compte gratuitement", key="cta_final_register", use_container_width=True, type="primary"):
            track_cta_landing_click("Créer mon compte gratuitement", source="footer_cta")
            st.switch_page("pages/1_Login.py")

st.markdown("<br>", unsafe_allow_html=True)

# 9. FOOTER
st.markdown(
    """<div style="border-top: 1px solid #E5E7EB; padding: 30px 20px; margin-top: 20px;">
        <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 16px;
            max-width: 800px; margin: 0 auto;">
            <div>
                <div style="font-weight: 700; color: #1A3D22; font-size: 16px;">ESG Optimizer AI</div>
                <div style="font-size: 12px; color: #9CA3AF; margin-top: 4px;">
                    Analyse ESG automatisée par IA
                </div>
            </div>
            <div style="font-size: 12px; color: #9CA3AF; line-height: 2;">
                <a href="/7_Mentions" style="color: #6B7280; text-decoration: none;">Mentions légales</a><br>
                <a href="/7_Mentions#cgu" style="color: #6B7280; text-decoration: none;">CGU</a><br>
                <a href="/7_Mentions#confidentialite" style="color: #6B7280; text-decoration: none;">Politique de confidentialité</a>
            </div>
            <div style="font-size: 12px; color: #9CA3AF; line-height: 2;">
                <a href="mailto:contact@esg-optimizer.fr" style="color: #6B7280; text-decoration: none;">Contact</a><br>
                Conforme ESRS E1-E5, S1-S4, G1<br>
                Hébergement UE
            </div>
        </div>
        <div style="text-align: center; font-size: 11px; color: #D1D5DB; margin-top: 20px;">
            © 2026 ESG Optimizer AI - Tous droits réservés
        </div>
    </div>""",
    unsafe_allow_html=True,
)
