"""
ESG Optimizer - Router admin.
Deux modes d'autorisation :
  1. Header X-Admin-Key (CRON_API_KEY) pour les scripts internes.
  2. Token utilisateur (Clerk ou JWT) avec email dans la liste ADMIN_EMAILS.
"""

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db
from backend.models import Analysis, Company, User
from backend.routers.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


# ---- helpers d'autorisation -------------------------------------------------

def _require_admin_key(x_admin_key: str = Header(...)):
    """Vérifie le header X-Admin-Key (CRON_API_KEY)."""
    expected = settings.cron_api_key or settings.jwt_secret
    if not expected or expected == "CHANGE_ME":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin non configuré.",
        )
    if x_admin_key != expected:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Clé admin invalide.")


def _require_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Vérifie que l'utilisateur connecté est dans la liste des admins."""
    if current_user.email.lower() not in settings.admin_email_list:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs.",
        )
    return current_user


# ---- endpoints protégés par clé API (usage interne / cron) ------------------

@router.post("/reset-quota/{user_id}", dependencies=[Depends(_require_admin_key)])
def reset_user_quota(user_id: int, db: Session = Depends(get_db)):
    """Remet à zéro le compteur analyses_this_month d'un utilisateur."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    old = user.analyses_this_month
    user.analyses_this_month = 0
    db.commit()
    logger.info("Admin: quota reset user=%d (%d -> 0)", user_id, old)
    return {"status": "ok", "user_id": user_id, "before": old, "after": 0}


@router.get("/users", dependencies=[Depends(_require_admin_key)])
def list_users_key(db: Session = Depends(get_db)):
    """Liste tous les utilisateurs (accès via clé API)."""
    return _users_list(db)


# ---- endpoints protégés par token utilisateur admin ------------------------

@router.get("/me")
def admin_me(current_user: User = Depends(_require_admin_user)):
    """Vérifie si l'utilisateur connecté est admin."""
    return {
        "is_admin": True,
        "email": current_user.email,
        "id": current_user.id,
    }


@router.get("/dashboard")
def admin_dashboard(
    current_user: User = Depends(_require_admin_user),
    db: Session = Depends(get_db),
):
    """Stats globales pour l'interface admin."""
    total_users = db.query(User).count()
    total_analyses = db.query(Analysis).count()
    success_analyses = db.query(Analysis).filter(Analysis.status == "success").count()
    pending_analyses = db.query(Analysis).filter(
        Analysis.status.in_(["pending", "processing"])
    ).count()

    return {
        "total_users": total_users,
        "total_analyses": total_analyses,
        "success_analyses": success_analyses,
        "pending_analyses": pending_analyses,
    }


@router.get("/all-users")
def admin_list_users(
    current_user: User = Depends(_require_admin_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
):
    """Liste paginée de tous les utilisateurs."""
    return _users_list(db, page=page, per_page=per_page)


@router.get("/all-analyses")
def admin_list_analyses(
    current_user: User = Depends(_require_admin_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
):
    """Liste paginée de toutes les analyses (tous utilisateurs)."""
    rows = (
        db.query(Analysis, Company.name, User.email)
        .join(Company, Analysis.company_id == Company.id)
        .join(User, Analysis.user_id == User.id)
        .order_by(Analysis.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    total = db.query(Analysis).count()
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "analyses": [
            {
                "id": a.id,
                "company_name": cname,
                "user_email": uemail,
                "user_id": a.user_id,
                "report_year": a.report_year,
                "score_global": a.score_global,
                "status": a.status,
                "created_at": str(a.created_at),
            }
            for a, cname, uemail in rows
        ],
    }


@router.post("/reassign-analysis/{analysis_id}")
def admin_reassign_analysis(
    analysis_id: int,
    target_email: str = Query(..., description="Email du compte cible"),
    current_user: User = Depends(_require_admin_user),
    db: Session = Depends(get_db),
):
    """
    Réassigne une analyse à un autre utilisateur (correction de migration).
    Utile quand une analyse appartient à l'ancien compte Streamlit au lieu du compte Clerk.
    """
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse introuvable.")

    target_user = db.query(User).filter(User.email == target_email).first()
    if not target_user:
        raise HTTPException(status_code=404, detail=f"Utilisateur '{target_email}' introuvable.")

    old_user_id = analysis.user_id
    analysis.user_id = target_user.id

    # Réassigner aussi la company si elle appartient à l'ancien user
    company = db.query(Company).filter(Company.id == analysis.company_id).first()
    if company and company.user_id == old_user_id:
        company.user_id = target_user.id

    db.commit()
    logger.info(
        "Admin: analyse [%d] réassignée de user_id=%d à user_id=%d (%s)",
        analysis_id, old_user_id, target_user.id, target_email,
    )
    return {
        "status": "ok",
        "analysis_id": analysis_id,
        "old_user_id": old_user_id,
        "new_user_id": target_user.id,
        "new_user_email": target_user.email,
    }


@router.post("/set-plan/{user_id}")
def admin_set_plan(
    user_id: int,
    plan: str = Query(..., description="Plan: discovery | essential | pro | enterprise"),
    current_user: User = Depends(_require_admin_user),
    db: Session = Depends(get_db),
):
    """Change le plan d'un utilisateur."""
    valid_plans = {"discovery", "free", "essential", "pro", "enterprise"}
    if plan not in valid_plans:
        raise HTTPException(status_code=400, detail=f"Plan invalide. Valeurs: {valid_plans}")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    old_plan = user.plan
    user.plan = plan
    db.commit()
    logger.info("Admin: plan user=%d changé de '%s' à '%s'", user_id, old_plan, plan)
    return {"status": "ok", "user_id": user_id, "old_plan": old_plan, "new_plan": plan}


@router.post("/reset-quota-admin/{user_id}")
def admin_reset_quota(
    user_id: int,
    current_user: User = Depends(_require_admin_user),
    db: Session = Depends(get_db),
):
    """Remet à zéro le compteur analyses_this_month (accès admin par token)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    old = user.analyses_this_month
    user.analyses_this_month = 0
    db.commit()
    return {"status": "ok", "user_id": user_id, "before": old, "after": 0}


@router.post("/set-plan-by-email")
def admin_set_plan_by_email(
    email: str = Query(..., description="Email de l'utilisateur"),
    plan: str = Query(..., description="Plan: discovery | essential | pro | enterprise"),
    reset_quota: bool = Query(False, description="Remet aussi analyses_this_month a 0"),
    current_user: User = Depends(_require_admin_user),
    db: Session = Depends(get_db),
):
    """Change le plan d'un utilisateur identifie par son email (+ reset quota optionnel)."""
    valid_plans = {"discovery", "free", "essential", "pro", "enterprise"}
    if plan not in valid_plans:
        raise HTTPException(status_code=400, detail=f"Plan invalide. Valeurs: {valid_plans}")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"Utilisateur '{email}' introuvable.")

    old_plan = user.plan
    old_quota = user.analyses_this_month
    user.plan = plan
    if reset_quota:
        user.analyses_this_month = 0
    db.commit()
    logger.info(
        "Admin: plan user=%d (%s) change de '%s' a '%s'%s",
        user.id, email, old_plan, plan,
        f" + quota reset ({old_quota}->0)" if reset_quota else "",
    )
    return {
        "status": "ok",
        "user_id": user.id,
        "email": email,
        "old_plan": old_plan,
        "new_plan": plan,
        "quota_reset": reset_quota,
        "analyses_this_month": user.analyses_this_month,
    }


@router.post("/reset-all-analyses", dependencies=[Depends(_require_admin_key)])
def admin_reset_all_analyses(
    db: Session = Depends(get_db),
):
    """Supprime toutes les analyses et remet les quotas a zero (admin uniquement)."""
    total_deleted = db.query(Analysis).delete()
    db.query(Company).delete()
    users = db.query(User).all()
    for u in users:
        u.analyses_this_month = 0
        u.total_analyses = 0 if hasattr(u, "total_analyses") else u.analyses_this_month
    db.commit()
    logger.info("Admin: RESET TOTAL — %d analyses supprimees", total_deleted)
    return {
        "status": "ok",
        "analyses_deleted": total_deleted,
        "message": f"{total_deleted} analyses supprimees, quotas remis a zero.",
    }


@router.patch("/fix-email")
def admin_fix_email(
    old_email: str = Query(...),
    new_email: str = Query(...),
    current_user: User = Depends(_require_admin_user),
    db: Session = Depends(get_db),
):
    """
    Corrige l'email d'un utilisateur (ex: migrer {clerk_id}@clerk.local vers le vrai email).
    """
    user = db.query(User).filter(User.email == old_email).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"Utilisateur '{old_email}' introuvable.")

    # Vérifier qu'il n'y a pas de collision avec un autre compte
    conflict = db.query(User).filter(User.email == new_email, User.id != user.id).first()
    if conflict:
        raise HTTPException(
            status_code=409,
            detail=f"'{new_email}' est déjà utilisé par user_id={conflict.id}.",
        )

    old = user.email
    user.email = new_email
    db.commit()
    logger.info("Admin: email user=%d changé de '%s' à '%s'", user.id, old, new_email)
    return {"status": "ok", "user_id": user.id, "old_email": old, "new_email": new_email}


# ---- helper privé -----------------------------------------------------------

def _users_list(db: Session, page: int = 1, per_page: int = 100):
    users = (
        db.query(User)
        .order_by(User.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    total = db.query(User).count()
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "plan": u.plan,
                "analyses_this_month": u.analyses_this_month,
                "clerk_id": u.clerk_id,
                "created_at": str(u.created_at),
            }
            for u in users
        ],
    }
