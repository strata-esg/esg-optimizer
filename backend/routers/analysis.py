"""
ESG Optimizer - Router analyse.
POST /analysis/upload  : lance l'analyse en arrière-plan
GET  /analysis/{id}    : récupère les résultats
"""

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
from backend.services.reporter import generate_analysis_pdf, generate_delta_pdf, generate_preview
from backend.services.badge_generator import generate_badge
from backend.services.storage_service import StorageService
from backend.services.analytics_service import ph

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["analysis"])


def _dispatch_analysis(analysis_id: int, storage_key: str, background_tasks) -> None:
    """
    Dispatch le pipeline d'analyse :
    - Si ENABLE_CELERY=true ET REDIS_URL configure : tache Celery (worker isole, pas de timeout HTTP).
    - Sinon : BackgroundTasks FastAPI (mode defaut sans Celery, adapte au plan Railway actuel).
    """
    if settings.enable_celery and settings.redis_url:
        try:
            from backend.tasks.analysis_task import run_analysis_task
            run_analysis_task.delay(analysis_id, storage_key)
            logger.info("Analyse [%d] dispatchee vers Celery (Redis configure)", analysis_id)
            return
        except ImportError as exc:
            logger.warning(
                "Celery non installe (%s) - fallback BackgroundTasks pour analyse [%d]",
                exc, analysis_id,
            )
    background_tasks.add_task(_run_pipeline_with_own_session, analysis_id, storage_key)
    logger.info("Analyse [%d] via BackgroundTasks", analysis_id)


def _check_quota(user: User) -> None:
    # PostHog : quota atteint = signal de conversion fort
    """
    Vérifie le quota d'analyses selon le plan :
    - discovery / free : 1 analyse au total
    - essential : paiement à l'unité (vérifié via Stripe, pas de quota ici pour l'instant)
    - pro / enterprise : illimité
    Les admins (emails dans ADMIN_EMAILS) ne sont jamais bloqués par le quota.
    """
    if user.email.lower() in settings.admin_email_list:
        return
    if user.plan in ("discovery", "free"):
        if user.analyses_this_month >= settings.discovery_total_limit:
            ph.capture(user.id, "quota_hit", {
                "plan": user.plan,
                "analyses_used": user.analyses_this_month,
                "limit": settings.discovery_total_limit,
            })
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

    # Sauvegarder le fichier (R2 en prod, tempfile local en dev)
    storage_key = StorageService.upload(content, file.filename)

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

    # 6. Lancer le pipeline (Celery si Redis configure, BackgroundTasks sinon)
    logger.info(
        "Analyse [%d] creee - user=%d, company=%s, fichier=%s, storage_key=%s",
        analysis.id, current_user.id, company_name, file.filename, storage_key,
    )
    _dispatch_analysis(analysis.id, storage_key, background_tasks)

    # 7. Incrémenter le compteur seulement si le dispatch a reussi
    current_user.analyses_this_month += 1
    db.commit()

    # PostHog : analyse lancée (event de funnel critique)
    ph.capture(current_user.id, "analysis_started", {
        "analysis_id": analysis.id,
        "format": file_format,
        "sector": sector or "non_precise",
        "plan": current_user.plan,
    })

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

    company = db.query(Company).filter(Company.id == analysis.company_id).first()
    return _serialize_analysis(analysis, company.name if company else None)


def _serialize_analysis(analysis: Analysis, company_name: str | None = None) -> dict:
    """Convertit les champs JSON string en objets Python pour la réponse."""
    return {
        "id": analysis.id,
        "company_id": analysis.company_id,
        "company_name": company_name,
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
        "share_token": analysis.share_token,
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


# GET /analysis/{analysis_id}/preview-pdf : disponible tous plans (watermark PREVISUALISATION)
@router.get("/{analysis_id}/preview-pdf")
def download_preview_pdf(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Télécharge l'aperçu PDF 3 pages avec watermark PRÉVISUALISATION.
    Disponible pour tous les plans, y compris Découverte.
    """
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
        pdf_bytes = generate_preview(analysis, company)
    except Exception as exc:
        logger.error("Erreur génération preview PDF [%d] : %s", analysis_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération de l'aperçu PDF : {exc}",
        )

    filename = f"ESG_Preview_{company.name}_{analysis.report_year or 'NA'}.pdf"
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
# PUBLIC : pas d'auth, sécurisé par share_token UUID non-devinable
@router.get("/badge/{share_token}")
def get_badge(share_token: str, db: Session = Depends(get_db)):
    """
    Génère et retourne le badge PNG pour le partage social.
    Endpoint public : pas besoin d'auth, le share_token est un UUID unique.
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


# POST /analysis/{id}/recompute-delta
@router.post("/{analysis_id}/recompute-delta")
def recompute_delta(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Recalcule le delta pour une analyse existante.
    Utile quand l'analyse a été effectuée avant qu'une analyse précédente existe.
    Réservé aux plans payants (essential, pro, enterprise).
    """
    if current_user.plan in ("discovery", "free"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Le Delta Report est disponible à partir du plan Essentiel.",
        )

    analysis = (
        db.query(Analysis)
        .filter(Analysis.id == analysis_id, Analysis.user_id == current_user.id,
                Analysis.status == "success")
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analyse introuvable.")

    previous = find_previous_analysis(db, analysis)
    if not previous:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucune analyse précédente trouvée pour cette entreprise.",
        )

    try:
        delta_result = run_delta(analysis, db)
    except Exception as exc:
        logger.error("Recompute delta [%d] : %s", analysis_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du calcul du delta : {exc}",
        )

    if delta_result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucune analyse précédente trouvée pour cette entreprise.",
        )

    return {"status": "ok", "analysis_id": analysis_id, "previous_id": previous.id}
