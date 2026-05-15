"""
ESG Optimizer MVP - Router Email.
POST /email/weekly-digest     -> Envoie le digest hebdomadaire (cron ou manuel)
PUT  /email/preferences       -> Met à jour les préférences email
GET  /email/preferences       -> Récupère les préférences email
"""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db
from backend.models import Analysis, Company, User
from backend.routers.auth import get_current_user
from backend.services.email_service import send_weekly_digest_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email", tags=["email"])


# SCHEMAS

class EmailPreferences(BaseModel):
    email_notifications: bool


# GET /email/preferences

@router.get("/preferences")
def get_email_preferences(current_user: User = Depends(get_current_user)):
    """Retourne les préférences email de l'utilisateur."""
    return {"email_notifications": current_user.email_notifications}


# PUT /email/preferences

@router.put("/preferences")
def update_email_preferences(
    body: EmailPreferences,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Met à jour les préférences email."""
    current_user.email_notifications = body.email_notifications
    db.commit()
    logger.info("User %d - email_notifications = %s", current_user.id, body.email_notifications)
    return {"email_notifications": current_user.email_notifications}


# POST /email/weekly-digest - Digest hebdomadaire

@router.post("/weekly-digest")
def trigger_weekly_digest(
    api_key: str = Query(..., description="Clé API pour sécuriser l'endpoint cron"),
    db: Session = Depends(get_db),
):
    """
    Envoie le digest hebdomadaire à tous les utilisateurs opt-in.
    Sécurisé par une clé API (à appeler via cron ou manuellement).
    Utilise JWT_SECRET comme clé pour simplifier - en prod, ajouter une clé dédiée.
    """
    # Utiliser CRON_API_KEY dédiée (et non JWT_SECRET qui est un secret critique)
    valid_key = settings.cron_api_key or settings.jwt_secret  # fallback pour rétro-compat
    if not valid_key or api_key != valid_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clé API invalide.",
        )

    # Trouver tous les utilisateurs avec notifications activées
    users = (
        db.query(User)
        .filter(User.email_notifications == True)
        .all()
    )

    sent_count = 0
    error_count = 0

    for user in users:
        try:
            # Stats agrégées de l'utilisateur
            total = db.query(func.count(Analysis.id)).filter(
                Analysis.user_id == user.id,
                Analysis.status == "success",
            ).scalar() or 0

            if total == 0:
                continue  # Pas d'analyses -> pas de digest

            avg_score = db.query(func.avg(Analysis.score_global)).filter(
                Analysis.user_id == user.id,
                Analysis.status == "success",
                Analysis.score_global.isnot(None),
            ).scalar()

            csrd_total = db.query(func.count(Analysis.id)).filter(
                Analysis.user_id == user.id,
                Analysis.status == "success",
                Analysis.csrd_ready.isnot(None),
            ).scalar() or 1

            csrd_ready_count = db.query(func.count(Analysis.id)).filter(
                Analysis.user_id == user.id,
                Analysis.status == "success",
                Analysis.csrd_ready == True,
            ).scalar() or 0

            csrd_pct = (csrd_ready_count / csrd_total * 100) if csrd_total > 0 else None

            # 5 dernières analyses (avec nom de la company)
            latest = (
                db.query(Analysis, Company.name.label("company_name"))
                .join(Company, Company.id == Analysis.company_id)
                .filter(Analysis.user_id == user.id, Analysis.status == "success")
                .order_by(Analysis.created_at.desc())
                .limit(5)
                .all()
            )

            latest_list = [
                {
                    "company_name": row.company_name,
                    "score_global": row.Analysis.score_global,
                    "csrd_ready": row.Analysis.csrd_ready,
                }
                for row in latest
            ]

            success = send_weekly_digest_email(
                email=user.email,
                total_analyses=total,
                avg_score=avg_score,
                csrd_ready_pct=csrd_pct,
                latest_analyses=latest_list,
            )

            if success:
                sent_count += 1
            else:
                error_count += 1

        except Exception as e:
            logger.error("Digest user %d erreur : %s", user.id, e)
            error_count += 1

    logger.info("Weekly digest - %d envoyés, %d erreurs sur %d users", sent_count, error_count, len(users))
    return {
        "status": "ok",
        "total_users": len(users),
        "sent": sent_count,
        "errors": error_count,
    }
