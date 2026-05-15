"""
ESG Optimizer MVP - Composant Onboarding 3 étapes.
Affiché après la première inscription pour qualifier l'utilisateur
et le guider vers sa première analyse.
"""

import streamlit as st


ROLES = [
    ("pme", "PME / ETI", "Je prépare ma conformité CSRD"),
    ("consultant", "Consultant ESG", "J'analyse des rapports pour mes clients"),
    ("drse", "Directeur RSE", "Je pilote la performance ESG de mon entreprise"),
    ("investisseur", "Investisseur / Analyste", "J'évalue des portefeuilles ESG"),
    ("autre", "Autre", "J'explore le sujet"),
]

REPORT_TYPES = [
    ("dpef", "DPEF / Déclaration de Performance Extra-Financière"),
    ("rapport_rse", "Rapport RSE / Développement Durable"),
    ("rapport_integre", "Rapport Intégré (financier + extra-financier)"),
    ("bilan_carbone", "Bilan Carbone / Bilan GES"),
    ("rapport_csrd", "Rapport CSRD (premier exercice)"),
    ("ne_sais_pas", "Je ne sais pas encore"),
]


def render_onboarding() -> bool:
    """
    Affiche le wizard d'onboarding 3 étapes.
    Retourne True si l'onboarding est terminé.

    Stocke les réponses dans st.session_state["onboarding_data"].
    """
    if st.session_state.get("onboarding_complete"):
        return True

    if "onboarding_step" not in st.session_state:
        st.session_state["onboarding_step"] = 1
        st.session_state["onboarding_data"] = {}

    step = st.session_state["onboarding_step"]

    # Barre de progression visuelle
    st.markdown(
        f"""<div style="text-align: center; padding: 16px 0 24px 0;">
            <div style="font-family: 'DM Serif Display', Georgia, serif; font-size: 1.5rem;
                color: #1A3D22; margin-bottom: 16px;">Bienvenue sur ESG Optimizer</div>
            <div style="display: flex; justify-content: center; gap: 8px; align-items: center;">
                {"".join(
                    f'<div style="width: 48px; height: 4px; border-radius: 2px; background: {"#1A3D22" if i <= step else "#E5E7EB"};"></div>'
                    for i in range(1, 4)
                )}
            </div>
            <div style="font-size: 13px; color: #6B7280; margin-top: 8px;">
                Étape {step} sur 3
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    if step == 1:
        _step_role()
    elif step == 2:
        _step_report_type()
    elif step == 3:
        _step_first_action()

    return False


def _on_role_change():
    """Callback on_change : sélection du rôle -> avance automatiquement à l'étape 2."""
    val = st.session_state.get("ob_radio_role")
    if not val:
        return
    # Extraire la clé depuis le label "key - label - desc"
    for key, label, desc in ROLES:
        if val.startswith(label):
            st.session_state["onboarding_data"]["role"] = key
            break
    st.session_state["onboarding_step"] = 2


def _on_report_type_change():
    """Callback on_change : sélection du type -> avance automatiquement à l'étape 3."""
    val = st.session_state.get("ob_radio_rtype")
    if not val:
        return
    for key, label in REPORT_TYPES:
        if val == label:
            st.session_state["onboarding_data"]["report_type"] = key
            break
    st.session_state["onboarding_step"] = 3


def _step_role():
    """Étape 1 : Quel est votre profil ? (FIX #6 : on_change auto-advance)"""
    st.markdown("**Quel est votre profil ?**")
    st.caption("Cliquez sur votre profil pour passer directement à l'étape suivante.")

    role_options = [f"{label} - {desc}" for _, label, desc in ROLES]

    # Pré-sélectionner si déjà renseigné
    current_role = st.session_state["onboarding_data"].get("role")
    default_idx = 0
    if current_role:
        for i, (key, label, desc) in enumerate(ROLES):
            if key == current_role:
                default_idx = i
                break

    st.radio(
        "Profil",
        options=role_options,
        index=default_idx,
        key="ob_radio_role",
        on_change=_on_role_change,
        label_visibility="collapsed",
    )


def _step_report_type():
    """Étape 2 : Quel type de rapport ? (FIX #6 : on_change auto-advance)"""
    st.markdown("**Quel type de rapport allez-vous analyser ?**")
    st.caption("Cliquez pour passer directement à l'étape suivante.")

    report_options = [label for _, label in REPORT_TYPES]

    current_rtype = st.session_state["onboarding_data"].get("report_type")
    default_idx = 0
    if current_rtype:
        for i, (key, label) in enumerate(REPORT_TYPES):
            if key == current_rtype:
                default_idx = i
                break

    st.radio(
        "Type de rapport",
        options=report_options,
        index=default_idx,
        key="ob_radio_rtype",
        on_change=_on_report_type_change,
        label_visibility="collapsed",
    )

    st.markdown("")
    if st.button("← Retour", use_container_width=True, key="back_2"):
        st.session_state["onboarding_step"] = 1
        st.rerun()


def _step_first_action():
    """Étape 3 : Lancer la première action (upload ou rapport échantillon)."""
    st.markdown("**Prêt pour votre première analyse ?**")
    st.caption("Uploadez votre propre rapport ou essayez avec un rapport d'exemple.")

    st.markdown(
        """<div style="background: #F0FDF4; border: 1px solid #D4F0D8; border-radius: 12px;
            padding: 20px; margin: 16px 0;">
            <div style="font-weight: 600; color: #1A3D22; font-size: 15px;">
                Option 1 : Analyser mon rapport
            </div>
            <div style="font-size: 13px; color: #6B7280; margin-top: 4px;">
                Uploadez votre rapport de durabilité (PDF, DOCX ou XLSX) et obtenez
                votre diagnostic en 3 minutes.
            </div>
        </div>""",
        unsafe_allow_html=True,
    )
    if st.button("Uploader mon rapport", type="primary", use_container_width=True, key="go_upload"):
        st.session_state["onboarding_complete"] = True
        st.switch_page("pages/2_Upload.py")

    st.markdown(
        """<div style="background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 12px;
            padding: 20px; margin: 16px 0;">
            <div style="font-weight: 600; color: #374151; font-size: 15px;">
                Option 2 : Essayer avec un rapport d'exemple
            </div>
            <div style="font-size: 13px; color: #6B7280; margin-top: 4px;">
                Découvrez l'expérience avec un rapport de démonstration pré-chargé.
                Résultat instantané.
            </div>
        </div>""",
        unsafe_allow_html=True,
    )
    if st.button("Voir le rapport d'exemple", use_container_width=True, key="go_sample"):
        st.session_state["onboarding_complete"] = True
        st.session_state["use_sample_report"] = True
        st.switch_page("pages/2_Upload.py")

    st.markdown("")
    col_back2, col_skip = st.columns(2)
    with col_back2:
        if st.button("Retour", use_container_width=True, key="back_3"):
            st.session_state["onboarding_step"] = 2
            st.rerun()
    with col_skip:
        if st.button("Passer", use_container_width=True, key="skip_onboarding"):
            st.session_state["onboarding_complete"] = True
            st.rerun()
