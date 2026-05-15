"""
ESG Optimizer MVP - Router public (quick-check sans authentification).
POST /public/quick-check -> analyse rapide sans compte
GET  /public/quick-check/{token} -> récupérer le résultat
POST /auth/claim-analysis -> rattacher un quick-check à un compte user
"""

import hashlib
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db, SessionLocal
from backend.models import Analysis, Company, PublicAnalysis, User
from backend.prompts.system_quick_check import SYSTEM_QUICK_CHECK_PROMPT
from backend.services.extractor import extract_text, ALLOWED_EXTENSIONS
from backend.services.storage_service import StorageService
# Import différé de get_current_user dans la fonction claim pour éviter
# tout risque d'import circulaire au chargement des modules (auth -> public).
# Il n'y a pas de vraie circularité, mais on garde l'import tardif par précaution.

from openai import OpenAI

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public", tags=["public"])

_client = OpenAI(api_key=settings.openai_api_key)


# RATE LIMITING par IP (simple, basé sur la table public_analyses)

def _hash_ip(ip: str) -> str:
    """Hash SHA-256 de l'IP pour ne pas stocker l'IP en clair (RGPD)."""
    return hashlib.sha256(ip.encode()).hexdigest()


def _check_rate_limit(db: Session, ip_hash: str) -> None:
    """
    Vérifie le rate-limit par IP :
    - Max 3 quick-checks par jour
    - Max 10 par semaine
    """
    now = datetime.now(timezone.utc)

    # Compteur journalier
    day_ago = now - timedelta(days=1)
    daily_count = (
        db.query(PublicAnalysis)
        .filter(PublicAnalysis.ip_hash == ip_hash, PublicAnalysis.created_at >= day_ago)
        .count()
    )
    if daily_count >= settings.public_rate_limit_daily:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Limite atteinte : {settings.public_rate_limit_daily} analyses gratuites par jour. "
                   f"Créez un compte pour analyser davantage de rapports.",
        )

    # Compteur hebdomadaire
    week_ago = now - timedelta(weeks=1)
    weekly_count = (
        db.query(PublicAnalysis)
        .filter(PublicAnalysis.ip_hash == ip_hash, PublicAnalysis.created_at >= week_ago)
        .count()
    )
    if weekly_count >= settings.public_rate_limit_weekly:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Limite atteinte : {settings.public_rate_limit_weekly} analyses gratuites par semaine. "
                   f"Créez un compte pour des analyses illimitées.",
        )


# QUICK-CHECK GPT-4o (version allégée)

def _call_gpt4o_quick(text: str) -> dict:
    """Appelle GPT-4o avec le prompt quick-check raccourci."""
    try:
        response = _client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_QUICK_CHECK_PROMPT},
                {"role": "user", "content": f"Rapport :\n{text}"},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=1000,  # Beaucoup moins que l'analyse complète (4000)
        )
        raw = response.choices[0].message.content
        return json.loads(raw)
    except Exception as exc:
        logger.error("Quick-check GPT-4o erreur : %s", exc)
        raise RuntimeError(f"Erreur analyse IA : {exc}") from exc


def _run_quick_check_pipeline(public_analysis_id: int, storage_key: str) -> None:
    """
    Background task pour le quick-check.
    Crée sa propre session DB (celle du request est fermée).
    Télécharge le fichier depuis R2 (ou utilise le chemin local en dev).
    """
    db = SessionLocal()
    start = time.time()
    pa = None  # Initialisé à None pour éviter NameError dans le except block
    local_path: str | None = None

    try:
        pa = db.query(PublicAnalysis).filter(PublicAnalysis.id == public_analysis_id).first()
        if not pa:
            logger.error("PublicAnalysis %d introuvable", public_analysis_id)
            return

        pa.status = "processing"
        db.commit()

        # 1. Récupérer le fichier depuis le stockage
        local_path = StorageService.download_to_tempfile(storage_key)

        # 2. Extraction texte
        extension = Path(local_path).suffix.lstrip(".")
        text = extract_text(local_path, extension)

        if not text.strip():
            raise RuntimeError("Le document ne contient aucun texte exploitable.")

        # Tronquer pour le quick-check (moins de contexte nécessaire)
        text = text[:20_000]

        # 2. Appel GPT-4o
        result = _call_gpt4o_quick(text)

        # 3. Sauvegarde résultats
        pa.score_global = result.get("score_global")
        pa.csrd_ready = result.get("csrd_ready")
        pa.teaser_strengths = json.dumps(result.get("top_strengths", []), ensure_ascii=False)
        pa.teaser_weaknesses = json.dumps(result.get("top_weaknesses", []), ensure_ascii=False)
        pa.full_response = json.dumps(result, ensure_ascii=False)
        pa.status = "success"
        pa.processing_time_s = round(time.time() - start, 2)

        logger.info(
            "Quick-check [%d] - Succès en %.1fs (score: %s)",
            public_analysis_id, pa.processing_time_s, pa.score_global,
        )

    except Exception as exc:
        logger.error("Quick-check [%d] - Échec : %s", public_analysis_id, exc)
        if pa is not None:
            # pa a été trouvé en DB - on peut marquer l'échec
            pa.status = "failed"
            pa.error_message = str(exc)[:500]
            pa.processing_time_s = round(time.time() - start, 2)
        # Si pa est None (DB query elle-même a échoué), on ne peut rien persister

    finally:
        try:
            db.commit()
        except Exception as commit_exc:
            logger.error("Quick-check [%d] - Commit final échoué : %s", public_analysis_id, commit_exc)
        db.close()

        # Nettoyage : supprimer depuis le stockage R2 + tempfile local éventuel
        try:
            StorageService.delete(storage_key)
        except Exception as del_exc:
            logger.warning("Quick-check [%d] - Impossible de supprimer storage_key=%s : %s", public_analysis_id, storage_key, del_exc)

        if local_path and local_path != storage_key:
            try:
                Path(local_path).unlink(missing_ok=True)
            except OSError:
                pass


# ENDPOINTS

@router.post("/quick-check", status_code=status.HTTP_202_ACCEPTED)
async def quick_check(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Quick-check public : upload un PDF et reçoit un diagnostic rapide.
    Pas besoin de compte. Rate-limité par IP.
    Retourne un token pour récupérer le résultat via polling.
    """
    # 1. Identifier et rate-limiter l'IP
    client_ip = request.client.host if request.client else "unknown"
    ip_hash = _hash_ip(client_ip)
    _check_rate_limit(db, ip_hash)

    # 2. Valider le fichier
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier manquant.")

    extension = Path(file.filename).suffix.lower().strip(".")
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Format non supporté : '.{extension}'. Formats acceptés : {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # 3. Vérifier la taille (plus strict que l'upload authentifié)
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.public_upload_max_mb:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Fichier trop volumineux : {size_mb:.1f} MB (max {settings.public_upload_max_mb} MB).",
        )

    # 4. Sauvegarder dans le stockage (R2 en prod, tempfile local en dev)
    storage_key = StorageService.upload(content, file.filename)

    # 5. Créer l'entrée en DB
    pa = PublicAnalysis(ip_hash=ip_hash, source_filename=file.filename, status="pending")
    db.add(pa)
    db.commit()
    db.refresh(pa)

    # 6. Lancer le pipeline en background
    logger.info("Quick-check [%d] créé - IP=%s, fichier=%s, storage_key=%s", pa.id, ip_hash[:12], file.filename, storage_key)
    background_tasks.add_task(_run_quick_check_pipeline, pa.id, storage_key)

    return {
        "token": pa.token,
        "status": "processing",
        "message": "Analyse en cours. Utilisez GET /public/quick-check/{token} pour récupérer le résultat.",
    }


@router.get("/quick-check/{token}")
def get_quick_check_result(token: str, db: Session = Depends(get_db)):
    """
    Récupère le résultat d'un quick-check par son token.
    Le token expire après 72h.
    """
    pa = db.query(PublicAnalysis).filter(PublicAnalysis.token == token).first()

    if not pa:
        raise HTTPException(status_code=404, detail="Analyse introuvable. Le token est peut-être expiré.")

    # Vérifier expiration
    now = datetime.now(timezone.utc)
    if pa.expires_at and pa.expires_at.replace(tzinfo=timezone.utc) < now:
        raise HTTPException(status_code=410, detail="Ce résultat a expiré. Relancez une analyse.")

    result = {
        "token": pa.token,
        "status": pa.status,
        "score_global": pa.score_global,
        "csrd_ready": pa.csrd_ready,
    }

    if pa.status == "success":
        result["teaser_strengths"] = json.loads(pa.teaser_strengths) if pa.teaser_strengths else []
        result["teaser_weaknesses"] = json.loads(pa.teaser_weaknesses) if pa.teaser_weaknesses else []

    if pa.status == "failed":
        result["error_message"] = pa.error_message

    return result


# CLAIM - Rattacher un quick-check à un compte (dans auth router)
# Ce endpoint est ajouté au router auth pour la cohérence, mais
# la logique est ici pour garder le contexte.

claim_router = APIRouter(prefix="/auth", tags=["auth"])


_claim_oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _get_current_user_for_claim(
    token: str = Depends(_claim_oauth2),
    db: Session = Depends(get_db),
) -> User:
    """Dépendance JWT autonome pour le claim router (évite l'import circulaire au niveau module)."""
    from backend.services.auth_service import decode_access_token
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide ou expiré")
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur introuvable")
    return user


@claim_router.post("/claim-analysis")
def claim_analysis(
    qc_token: str,
    current_user: User = Depends(_get_current_user_for_claim),
    db: Session = Depends(get_db),
):
    """
    Rattache un quick-check public à un compte utilisateur après inscription.
    Le user passe le qc_token reçu lors du quick-check.
    Protégé par JWT - authentification requise.
    """
    pa = db.query(PublicAnalysis).filter(PublicAnalysis.token == qc_token).first()

    if not pa:
        raise HTTPException(status_code=404, detail="Token de quick-check introuvable ou expiré.")

    if pa.status != "success":
        raise HTTPException(status_code=400, detail="L'analyse n'est pas terminée.")

    if pa.claimed_by_user_id is not None:
        raise HTTPException(status_code=409, detail="Cette analyse a déjà été rattachée à un compte.")

    # Vérifier expiration
    now = datetime.now(timezone.utc)
    expires = pa.expires_at
    if expires:
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires < now:
            raise HTTPException(status_code=410, detail="Ce résultat a expiré.")

    # Rattacher l'analyse au user courant
    pa.claimed_by_user_id = current_user.id
    db.commit()

    logger.info(
        "Quick-check [token=%s] rattaché à user=%d",
        qc_token[:8], current_user.id,
    )

    return {
        "message": "Quick-check rattaché avec succès.",
        "score_global": pa.score_global,
        "csrd_ready": pa.csrd_ready,
        "full_response": json.loads(pa.full_response) if pa.full_response else None,
    }
