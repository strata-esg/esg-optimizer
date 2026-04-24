"""
ESG Optimizer MVP — Client HTTP vers le backend FastAPI.
Encapsule tous les appels API avec gestion automatique du JWT.
"""

import os
import requests
from typing import Any

# URL du backend — configurable via variable d'environnement
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")


class APIError(Exception):
    """Erreur retournée par l'API backend."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"[{status_code}] {detail}")


# HELPERS

def _headers(token: str | None = None) -> dict:
    """Construit les headers avec le JWT si fourni."""
    h = {"Accept": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _handle_response(resp: requests.Response) -> dict:
    """Parse la réponse JSON et lève APIError si erreur HTTP."""
    if resp.status_code >= 400:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        raise APIError(resp.status_code, detail)
    return resp.json()


def _handle_binary_response(resp: requests.Response) -> bytes:
    """Retourne le contenu binaire (PDF) ou lève APIError."""
    if resp.status_code >= 400:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        raise APIError(resp.status_code, detail)
    return resp.content


# AUTH

def register(email: str, password: str, company_name: str | None = None) -> dict:
    """
    POST /auth/register
    Retourne : {"user": {...}, "access_token": "...", "token_type": "bearer"}
    """
    payload = {"email": email, "password": password}
    if company_name:
        payload["company_name"] = company_name
    resp = requests.post(f"{BACKEND_URL}/auth/register", json=payload, timeout=10)
    return _handle_response(resp)


def login(email: str, password: str) -> dict:
    """
    POST /auth/login
    Retourne : {"access_token": "...", "token_type": "bearer"}
    """
    resp = requests.post(
        f"{BACKEND_URL}/auth/login",
        json={"email": email, "password": password},
        timeout=10,
    )
    return _handle_response(resp)


def get_me(token: str) -> dict:
    """
    GET /auth/me
    Retourne le profil utilisateur.
    """
    resp = requests.get(f"{BACKEND_URL}/auth/me", headers=_headers(token), timeout=10)
    return _handle_response(resp)


# ANALYSIS

def upload_analysis(
    token: str,
    file_bytes: bytes,
    filename: str,
    company_name: str,
    report_year: int,
    sector: str | None = None,
) -> dict:
    """
    POST /analysis/upload (multipart/form-data)
    Retourne : {"analysis_id": int, "status": "processing"}
    """
    files = {"file": (filename, file_bytes)}
    data: dict[str, Any] = {
        "company_name": company_name,
        "report_year": str(report_year),
    }
    if sector:
        data["sector"] = sector

    resp = requests.post(
        f"{BACKEND_URL}/analysis/upload",
        headers=_headers(token),
        files=files,
        data=data,
        timeout=30,
    )
    return _handle_response(resp)


def get_analysis(token: str, analysis_id: int) -> dict:
    """
    GET /analysis/{id}
    Retourne l'analyse complète (polling pendant le traitement).
    """
    resp = requests.get(
        f"{BACKEND_URL}/analysis/{analysis_id}",
        headers=_headers(token),
        timeout=15,
    )
    return _handle_response(resp)


def download_pdf(token: str, analysis_id: int) -> bytes:
    """
    GET /analysis/{id}/pdf
    Retourne le contenu binaire du rapport PDF.
    """
    resp = requests.get(
        f"{BACKEND_URL}/analysis/{analysis_id}/pdf",
        headers=_headers(token),
        timeout=30,
    )
    return _handle_binary_response(resp)


def download_preview_pdf(token: str, analysis_id: int) -> bytes:
    """
    GET /analysis/{id}/preview-pdf
    Aperçu PDF 3 pages watermarked — disponible pour tous les plans.
    """
    resp = requests.get(
        f"{BACKEND_URL}/analysis/{analysis_id}/preview-pdf",
        headers=_headers(token),
        timeout=30,
    )
    return _handle_binary_response(resp)


def download_delta_pdf(token: str, analysis_id: int) -> bytes:
    """
    GET /analysis/{id}/delta-pdf
    Retourne le contenu binaire du delta report PDF.
    """
    resp = requests.get(
        f"{BACKEND_URL}/analysis/{analysis_id}/delta-pdf",
        headers=_headers(token),
        timeout=30,
    )
    return _handle_binary_response(resp)


# HISTORY & DASHBOARD

def get_history(token: str, page: int = 1, per_page: int = 20) -> dict:
    """
    GET /history?page=...&per_page=...
    Retourne : {"analyses": [...], "total": int, "page": int, "per_page": int}
    """
    resp = requests.get(
        f"{BACKEND_URL}/history",
        headers=_headers(token),
        params={"page": page, "per_page": per_page},
        timeout=15,
    )
    return _handle_response(resp)


def get_companies(token: str) -> list[dict]:
    """
    GET /history/companies
    Retourne la liste des entreprises analysées.
    """
    resp = requests.get(
        f"{BACKEND_URL}/history/companies",
        headers=_headers(token),
        timeout=10,
    )
    return _handle_response(resp)


def get_stats(token: str) -> dict:
    """
    GET /history/stats
    Retourne les stats agrégées pour le dashboard.
    """
    resp = requests.get(
        f"{BACKEND_URL}/history/stats",
        headers=_headers(token),
        timeout=10,
    )
    return _handle_response(resp)


# PUBLIC — Quick-check (sans auth)

def quick_check_upload(file_bytes: bytes, filename: str) -> dict:
    """
    POST /public/quick-check (multipart/form-data, sans auth)
    Retourne : {"token": str, "status": "processing", "message": str}
    """
    files = {"file": (filename, file_bytes)}
    resp = requests.post(
        f"{BACKEND_URL}/public/quick-check",
        files=files,
        timeout=30,
    )
    return _handle_response(resp)


def quick_check_result(token: str) -> dict:
    """
    GET /public/quick-check/{token}
    Retourne le résultat du quick-check (polling).
    """
    resp = requests.get(
        f"{BACKEND_URL}/public/quick-check/{token}",
        timeout=15,
    )
    return _handle_response(resp)


def claim_quick_check(auth_token: str, qc_token: str) -> dict:
    """
    POST /auth/claim-analysis
    Rattache un quick-check public à un compte utilisateur.
    """
    resp = requests.post(
        f"{BACKEND_URL}/auth/claim-analysis",
        headers=_headers(auth_token),
        params={"token": qc_token},
        timeout=10,
    )
    return _handle_response(resp)


# SOCIAL SHARING

def get_share_info(token: str, analysis_id: int) -> dict:
    """
    GET /analysis/{id}/share-info
    Retourne share_token, company_name, score_global, csrd_ready, report_year.
    """
    resp = requests.get(
        f"{BACKEND_URL}/analysis/{analysis_id}/share-info",
        headers=_headers(token),
        timeout=10,
    )
    return _handle_response(resp)


# STRIPE — Upgrade & Subscription

def get_upgrade_url(token: str, plan: str) -> dict:
    """
    GET /stripe/upgrade-url?plan=essential|pro
    Retourne : {"url": "https://buy.stripe.com/...?prefilled_email=...", "plan": "..."}
    """
    resp = requests.get(
        f"{BACKEND_URL}/stripe/upgrade-url",
        headers=_headers(token),
        params={"plan": plan},
        timeout=10,
    )
    return _handle_response(resp)


def get_my_subscription(token: str) -> dict:
    """
    GET /stripe/my-subscription
    Retourne l'abonnement actif de l'utilisateur.
    """
    resp = requests.get(
        f"{BACKEND_URL}/stripe/my-subscription",
        headers=_headers(token),
        timeout=10,
    )
    return _handle_response(resp)


# EMAIL — Préférences

def get_email_preferences(token: str) -> dict:
    """GET /email/preferences"""
    resp = requests.get(
        f"{BACKEND_URL}/email/preferences",
        headers=_headers(token),
        timeout=10,
    )
    return _handle_response(resp)


def update_email_preferences(token: str, email_notifications: bool) -> dict:
    """PUT /email/preferences"""
    resp = requests.put(
        f"{BACKEND_URL}/email/preferences",
        headers=_headers(token),
        json={"email_notifications": email_notifications},
        timeout=10,
    )
    return _handle_response(resp)
