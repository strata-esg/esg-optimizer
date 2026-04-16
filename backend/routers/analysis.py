"""
ESG Optimizer MVP — Router analyse.
POST /analysis/upload  → lance l'analyse en background
GET  /analysis/{id}    → récupère les résultats
"""

import tempfile
import logging
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db, SessionLocal
from backend.models import Analysis, Company, User
from backend.routers.auth import get_current_user
from backend.schemas import AnalysisCreatedResponse, AnalysisResponse
from backend.services.analyzer import run_analysis_pipeline
from backend.services.extractor import ALLOWED_EXTENSIONS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["analysis"])


def _check_quota(user: User) -> None:
    """Vérifie le quota freemium (1 analyse/mois si plan=free)."""
    if user.plan == "free" and user.analyses_this_month >= settings.free_tier_monthly_limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Quota atteint : {settings.free_tier_monthly_limit} analyse(s)/mois "
                f"sur le plan gratuit. Passez en Pro pour des analyses illimitées."
            ),
        )


def _validate_file(file: UploadFile) -> str:
    """Valide l'extension du fichier. Retourne le format (pdf, docx, xlsx)."""
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nom de fichier manquant.")

    extension = Path(file.filename).suffix.lower().strip(".")
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Format non supporté : '.{extension}'. Formats acceptés : {', '.join(ALLOWED_EXTENSIONS)}",
        )
    return extension


def _get_or_create_company(db: Session, user: User, company_name: str, sector: str | None) -> Company:
    """Récupère ou crée l'entreprise pour cet utilisateur."""
    company = (
        db.query(Company)
        .filter(Company.user_id == user.id, Company.name == company_name)
        .first()
    )
    if not company:
        company = Company(user_id=user.id, name=company_name, sector=sector)
        db.add(company)
        db.commit()
        db.refresh(company)
    elif sector and not company.sector:
        # Mettre à jour le secteur si absent
        company.sector = sector
        db.commit()
    return company


def _run_pipeline_with_own_session(analysis_id: int, file_path: str) -> None:
    """
    Wrapper pour le background task.
    Crée sa propre session DB (la session du request est fermée après la réponse).
    """
    db = SessionLocal()
    try:
        run_analysis_pipeline(analysis_id, file_path, db)
    finally:
        db.close()


# ── POST /analysis/upload ──────────────────────────────────────
@router.post("/upload", response_model=AnalysisCreatedResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_analysis(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    company_name: str = Form(...),
    report_year: int = Form(...),
    sector: str = Form(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload un rapport ESG et lance l'analyse en arrière-plan.
    Retourne immédiatement l'analysis_id pour polling.
    """
    # 1. Vérifier quota freemium
    _check_quota(current_user)

    # 2. Valider le fichier
    file_format = _validate_file(file)

    # 3. Sauvegarder le fichier en temporaire
    suffix = f".{file_format}"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix="esg_") as tmp:
        content = await file.read()

        # Vérifier la taille
        size_mb = len(content) / (1024 * 1024)
        if size_mb > settings.max_upload_size_mb:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Fichier trop volumineux : {size_mb:.1f} MB (max {settings.max_upload_size_mb} MB).",
            )

        tmp.write(content)
        tmp_path = tmp.name

    # 4. Créer ou récupérer l'entreprise
    company = _get_or_create_company(db, current_user, company_name, sector)

    # 5. Créer l'entrée Analysis en DB (status=pending)
    analysis = Analysis(
        company_id=company.id,
        user_id=current_user.id,
        report_year=report_year,
        source_filename=file.filename,
        source_format=file_format,
        status="pending",
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    # 6. Incrémenter le compteur d'analyses du mois
    current_user.analyses_this_month += 1
    db.commit()

    # 7. Lancer le pipeline en background
    logger.info(
        "Analyse [%d] créée — user=%d, company=%s, fichier=%s",
        analysis.id, current_user.id, company_name, file.filename,
    )
    background_tasks.add_task(_run_pipeline_with_own_session, analysis.id, tmp_path)

    return AnalysisCreatedResponse(analysis_id=analysis.id, status="processing")


# ── GET /analysis/{analysis_id} ─────────────────────────────────
@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Récupère les résultats d'une analyse (polling depuis le frontend)."""
    analysis = (
        db.query(Analysis)
        .filter(Analysis.id == analysis_id, Analysis.user_id == current_user.id)
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analyse introuvable.")

    return _serialize_analysis(analysis)


def _serialize_analysis(analysis: Analysis) -> dict:
    """Convertit les champs JSON string en objets Python pour la réponse."""
    import json

    def _safe_json_loads(raw: str | None) -> list | dict | None:
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None

    return {
        "id": analysis.id,
        "company_id": analysis.company_id,
        "user_id": analysis.user_id,
        "report_year": analysis.report_year,
        "source_filename": analysis.source_filename,
        "source_format": analysis.source_format,
        "score_env": analysis.score_env,
        "score_social": analysis.score_social,
        "score_gov": analysis.score_gov,
        "score_global": analysis.score_global,
        "csrd_ready": analysis.csrd_ready,
        "csrd_coverage_pct": analysis.csrd_coverage_pct,
        "missing_disclosures": _safe_json_loads(analysis.missing_disclosures),
        "kpis_detected": _safe_json_loads(analysis.kpis_detected),
        "strengths": _safe_json_loads(analysis.strengths),
        "weaknesses": _safe_json_loads(analysis.weaknesses),
        "recommendations": _safe_json_loads(analysis.recommendations),
        "esrs_coverage": _safe_json_loads(analysis.esrs_coverage),
        "executive_summary": analysis.executive_summary,
        "delta_env": analysis.delta_env,
        "delta_social": analysis.delta_social,
        "delta_gov": analysis.delta_gov,
        "delta_global": analysis.delta_global,
        "delta_narrative": analysis.delta_narrative,
        "processing_time_s": analysis.processing_time_s,
        "status": analysis.status,
        "error_message": analysis.error_message,
        "created_at": analysis.created_at,
    }
