"""
ESG Optimizer MVP — Gestion de la session Streamlit.
Stocke/lit/supprime le token JWT et les infos utilisateur dans st.session_state.
"""

import streamlit as st


# Clés session_state
_TOKEN_KEY = "jwt_token"
_USER_KEY = "current_user"
_ANALYSIS_KEY = "last_analysis_id"


# Token JWT

def save_token(token: str) -> None:
    """Sauvegarde le token JWT dans la session."""
    st.session_state[_TOKEN_KEY] = token


def get_token() -> str | None:
    """Retourne le token JWT ou None si non connecté."""
    return st.session_state.get(_TOKEN_KEY)


def clear_token() -> None:
    """Supprime le token de la session."""
    st.session_state.pop(_TOKEN_KEY, None)


# Infos utilisateur

def save_user(user: dict) -> None:
    """Sauvegarde les infos utilisateur dans la session."""
    st.session_state[_USER_KEY] = user


def get_user() -> dict | None:
    """Retourne les infos utilisateur ou None."""
    return st.session_state.get(_USER_KEY)


def clear_user() -> None:
    """Supprime les infos utilisateur de la session."""
    st.session_state.pop(_USER_KEY, None)


# Dernière analyse

def save_last_analysis_id(analysis_id: int) -> None:
    """Mémorise l'ID de la dernière analyse lancée (pour rediriger vers Résultats)."""
    st.session_state[_ANALYSIS_KEY] = analysis_id


def get_last_analysis_id() -> int | None:
    """Retourne l'ID de la dernière analyse ou None."""
    return st.session_state.get(_ANALYSIS_KEY)


# Quick-check token (pour claim après inscription)

_QC_TOKEN_KEY = "quick_check_token"


def save_qc_token(token: str) -> None:
    """Sauvegarde le token du quick-check pour le rattacher après inscription."""
    st.session_state[_QC_TOKEN_KEY] = token


def get_qc_token() -> str | None:
    """Retourne le token quick-check ou None."""
    return st.session_state.get(_QC_TOKEN_KEY)


def clear_qc_token() -> None:
    """Supprime le token quick-check."""
    st.session_state.pop(_QC_TOKEN_KEY, None)


# Helpers

def is_logged_in() -> bool:
    """True si un token JWT est présent en session."""
    return get_token() is not None


def logout() -> None:
    """Déconnexion complète : supprime token + user + analyse + quick-check."""
    clear_token()
    clear_user()
    clear_qc_token()
    st.session_state.pop(_ANALYSIS_KEY, None)


def require_auth() -> bool:
    """
    Vérifie que l'utilisateur est connecté.
    Si non connecté, affiche un warning et retourne False.
    À utiliser en haut de chaque page protégée :
        if not require_auth():
            st.stop()
    """
    if not is_logged_in():
        st.warning("Veuillez vous connecter pour accéder à cette page.")
        st.page_link("pages/1_Login.py", label="Aller à la page de connexion", icon="🔐")
        return False
    return True
