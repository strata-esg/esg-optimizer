"""
ESG Optimizer - Router admin.
Endpoints protégés par CRON_API_KEY, réservés à l'opérationnel interne.
"""

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db
from backend.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin_key(x_admin_key: str = Header(...)):
    """Vérifie que la requête porte la CRON_API_KEY dans le header X-Admin-Key."""
    if not settings.cron_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin non configuré (CRON_API_KEY vide).",
        )
    if x_admin_key != settings.cron_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clé admin invalide.",
        )


@router.post("/reset-quota/{user_id}", dependencies=[Depends(_require_admin_key)])
def reset_user_quota(user_id: int, db: Session = Depends(get_db)):
    """
    Remet à zéro le compteur analyses_this_month d'un utilisateur.
    Header requis : X-Admin-Key: <CRON_API_KEY>
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")

    old_count = user.analyses_this_month
    user.analyses_this_month = 0
    db.commit()

    logger.info("Admin: quota reset user=%d (%d -> 0)", user_id, old_count)
    return {
        "status": "ok",
        "user_id": user_id,
        "analyses_this_month_before": old_count,
        "analyses_this_month_after": 0,
    }


@router.get("/users", dependencies=[Depends(_require_admin_key)])
def list_users(db: Session = Depends(get_db)):
    """Liste tous les utilisateurs avec leur plan et quota."""
    users = db.query(User).order_by(User.id).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "plan": u.plan,
            "analyses_this_month": u.analyses_this_month,
            "created_at": u.created_at,
        }
        for u in users
    ]
