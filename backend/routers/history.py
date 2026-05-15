"""
ESG Optimizer MVP - Router historique & dashboard.
GET /history           -> liste paginée des analyses
GET /history/companies -> liste des entreprises analysées
GET /history/stats     -> stats agrégées pour le dashboard
"""

from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Query

from backend.database import get_db
from backend.models import Analysis, Company, User
from backend.routers.auth import get_current_user
from backend.schemas import (
    AnalysisSummary,
    CompanyResponse,
    HistoryResponse,
    StatsResponse,
)

router = APIRouter(prefix="/history", tags=["history"])


# GET /history
@router.get("", response_model=HistoryResponse)
def list_analyses(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Liste paginée de toutes les analyses de l'utilisateur."""
    base_query = (
        db.query(Analysis, Company.name)
        .join(Company, Analysis.company_id == Company.id)
        .filter(Analysis.user_id == current_user.id)
        .order_by(Analysis.created_at.desc())
    )

    total = base_query.count()
    rows = base_query.offset((page - 1) * per_page).limit(per_page).all()

    analyses = [
        AnalysisSummary(
            id=a.id,
            company_name=company_name,
            report_year=a.report_year,
            score_global=a.score_global,
            csrd_ready=a.csrd_ready,
            status=a.status,
            created_at=a.created_at,
        )
        for a, company_name in rows
    ]

    return HistoryResponse(
        analyses=analyses,
        total=total,
        page=page,
        per_page=per_page,
    )


# GET /history/companies
@router.get("/companies", response_model=list[CompanyResponse])
def list_companies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Liste des entreprises analysées par l'utilisateur."""
    companies = (
        db.query(Company)
        .filter(Company.user_id == current_user.id)
        .order_by(Company.name)
        .all()
    )
    return [CompanyResponse.model_validate(c) for c in companies]


# GET /history/stats
@router.get("/stats", response_model=StatsResponse)
def get_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Stats agrégées pour le dashboard : totaux, moyennes, % CSRD ready."""
    success_filter = (
        db.query(Analysis)
        .filter(Analysis.user_id == current_user.id, Analysis.status == "success")
    )

    total = success_filter.count()

    if total == 0:
        return StatsResponse(
            total_analyses=0,
            avg_score_env=None,
            avg_score_social=None,
            avg_score_gov=None,
            avg_score_global=None,
            csrd_ready_pct=None,
        )

    avgs = (
        db.query(
            func.avg(Analysis.score_env),
            func.avg(Analysis.score_social),
            func.avg(Analysis.score_gov),
            func.avg(Analysis.score_global),
        )
        .filter(Analysis.user_id == current_user.id, Analysis.status == "success")
        .first()
    )

    csrd_ready_count = (
        db.query(func.count(Analysis.id))
        .filter(
            Analysis.user_id == current_user.id,
            Analysis.status == "success",
            Analysis.csrd_ready == True,  # noqa: E712
        )
        .scalar()
    )

    return StatsResponse(
        total_analyses=total,
        avg_score_env=round(avgs[0], 1) if avgs[0] else None,
        avg_score_social=round(avgs[1], 1) if avgs[1] else None,
        avg_score_gov=round(avgs[2], 1) if avgs[2] else None,
        avg_score_global=round(avgs[3], 1) if avgs[3] else None,
        csrd_ready_pct=round((csrd_ready_count / total) * 100, 1) if total > 0 else None,
    )
