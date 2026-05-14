"""
ESG Optimizer — Tache Celery : pipeline d'analyse ESG.

Chaque analyse GPT-4o tourne dans un worker isole.
Le worker met a jour le statut en DB directement (pending -> processing -> success/error).
Le frontend poll GET /analysis/{id} pour savoir quand c'est pret.
"""

import logging

from backend.celery_app import celery_app
from backend.database import SessionLocal
from backend.services.analyzer import run_analysis_pipeline

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="analysis.run_pipeline",
    max_retries=1,
    default_retry_delay=10,
)
def run_analysis_task(self, analysis_id: int, storage_key: str) -> dict:
    """
    Lance le pipeline d'analyse ESG dans un worker Celery.

    Args:
        analysis_id: ID de l'analyse en DB (status=pending a l'entree).
        storage_key: Cle R2/chemin local du fichier uploade.

    Returns:
        dict avec analysis_id et status final.
    """
    logger.info("Celery task demarree : analysis_id=%d, key=%s", analysis_id, storage_key)

    db = SessionLocal()
    try:
        run_analysis_pipeline(analysis_id, storage_key, db)
        logger.info("Celery task terminee : analysis_id=%d", analysis_id)
        return {"analysis_id": analysis_id, "status": "success"}

    except Exception as exc:
        logger.error(
            "Celery task echouee : analysis_id=%d, erreur=%s",
            analysis_id,
            str(exc),
            exc_info=True,
        )
        # On laisse run_analysis_pipeline ecrire le status=error en DB
        # On ne retry pas les analyses (couteux, l'utilisateur doit re-uploader)
        raise

    finally:
        db.close()
