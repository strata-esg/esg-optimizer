"""
ESG Optimizer MVP — Router analyse.
POST /analysis/upload  → lance l'analyse en background
GET  /analysis/{id}    → récupère les résultats
"""

import tempfile
import logging
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db, SessionLocal
from backend.models import Analysis, Company, User
from backend.routers.auth import get_current_user
from backend.schemas import AnalysisCreatedResponse, AnalysisResponse, DeltaFullResponse
from backend.services.analyzer import run_analysis_pipeline
from backend.services.delta_service import find_previous_analysis, run_delta
from backend.utils import safe_json_loads as _safe_json_loads
from backend.services.extractor import ALLOWED_EXTENSIONS
from backend.services.reporter import generate_analysis_pdf, generate_delta_pdf
from backend.services.badge_generator import generate_badge

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["analysis"])


def _check_quota(user: User) -> None:
    """
    Vérifie le quota d'analyses selon le plan :
    - discovery / free : 1 analyse au total
    - essential : paiement à l'unité (vérifié via Stripe, pas de quota ici pour l'instant)
    - pro / enterprise : illimité
    """
    if user.plan in ("discovery", "free"):
        if user.analyses_this_month >= settings.discovery_total_limit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Quota atteint : {settings.discovery_total_limit} analyse gratuite. "
                    f"Passez au plan Essentiel (39€/analyse) ou Pro (129€/mois) "
                    f"pour continuer vos analyses."
                ),
            )
    # essential, pro, enterprise : pas de quota côté serveur (géré par Stripe/abonnement)


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


# POST /analysis/upload
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

    # 3. Lire le contenu et vérifier la taille AVANT de créer le fichier temporaire
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.max_upload_size_mb:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Fichier trop volumineux : {size_mb:.1f} MB (max {settings.max_upload_size_mb} MB).",
        )

    # Sauvegarder le fichier en temporaire (après validation de la taille)
    suffix = f".{file_format}"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix="esg_") as tmp:
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


# GET /analysis/{analysis_id}
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


# GET /analysis/{analysis_id}/pdf
@router.get("/{analysis_id}/pdf")
def download_analysis_pdf(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Télécharge le rapport PDF d'une analyse ESG."""
    analysis = (
        db.query(Analysis)
        .filter(Analysis.id == analysis_id, Analysis.user_id == current_user.id)
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analyse introuvable.")

    if analysis.status != "success":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"L'analyse n'est pas terminée (status: {analysis.status}).",
        )

    company = db.query(Company).filter(Company.id == analysis.company_id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entreprise introuvable.")

    try:
        pdf_bytes = generate_analysis_pdf(analysis, company)
    except Exception as exc:
        logger.error("Erreur génération PDF [%d] : %s", analysis_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération du PDF : {exc}",
        )

    filename = f"ESG_Report_{company.name}_{analysis.report_year or 'NA'}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# GET /analysis/{analysis_id}/delta-pdf
@router.get("/{analysis_id}/delta-pdf")
def download_delta_pdf(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Télécharge le rapport PDF delta (comparaison N vs N-1)."""
    analysis = (
        db.query(Analysis)
        .filter(Analysis.id == analysis_id, Analysis.user_id == current_user.id)
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analyse introuvable.")

    if analysis.status != "success":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"L'analyse n'est pas terminée (status: {analysis.status}).",
        )

    # Vérifier qu'un delta existe
    if analysis.delta_narrative is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun delta disponible pour cette analyse. "
                   "Un delta nécessite au moins deux analyses de la même entreprise.",
        )

    company = db.query(Company).filter(Company.id == analysis.company_id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entreprise introuvable.")

    previous = find_previous_analysis(db, analysis)
    if not previous:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analyse précédente introuvable pour générer le delta PDF.",
        )

    delta_narrative = _safe_json_loads(analysis.delta_narrative) or {}

    try:
        pdf_bytes = generate_delta_pdf(analysis, previous, company, delta_narrative)
    except Exception as exc:
        logger.error("Erreur génération delta PDF [%d] : %s", analysis_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération du delta PDF : {exc}",
        )

    filename = f"ESG_Delta_{company.name}_{previous.report_year or 'NA'}_vs_{analysis.report_year or 'NA'}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# GET /analysis/badge/{share_token}
# PUBLIC — pas d'auth, sécurisé par share_token UUID non-devinable
@router.get("/badge/{share_token}")
def get_badge(share_token: str, db: Session = Depends(get_db)):
    """
    Génère et retourne le badge PNG pour le partage social.
    Endpoint public — pas besoin d'auth, le share_token est un UUID unique.
    """
    analysis = (
        db.query(Analysis)
        .filter(Analysis.share_token == share_token, Analysis.status == "success")
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analyse introuvable.")

    company = db.query(Company).filter(Company.id == analysis.company_id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entreprise introuvable.")

    try:
        png_bytes = generate_badge(
            company_name=company.name,
            score_global=analysis.score_global or 0,
            csrd_ready=analysis.csrd_ready or False,
            report_year=analysis.report_year,
            analysis_date=analysis.created_at,
        )
    except Exception as exc:
        logger.error("Erreur génération badge [%s] : %s", share_token, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la génération du badge.",
        )

    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={
            "Cache-Control": "public, max-age=86400",  # Cache 24h
            "Content-Disposition": f'inline; filename="esg_badge_{company.name}.png"',
        },
    )


# GET /analysis/{id}/share-info
@router.get("/{analysis_id}/share-info")
def get_share_info(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retourne les infos nécessaires pour construire le lien de partage."""
    analysis = (
        db.query(Analysis)
        .filter(Analysis.id == analysis_id, Analysis.user_id == current_user.id)
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analyse introuvable.")

    company = db.query(Company).filter(Company.id == analysis.company_id).first()

    return {
        "share_token": analysis.share_token,
        "company_name": company.name if company else "Entreprise",
        "score_global": analysis.score_global,
        "csrd_ready": analysis.csrd_ready,
        "report_year": analysis.report_year,
    }
