"""
ESG Optimizer MVP - Service d'analyse GPT-4o.
Orchestre : extraction texte -> appel LLM -> parsing JSON -> sauvegarde DB.
"""

import json
import logging
import time
from pathlib import Path

from openai import OpenAI
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models import Analysis, Company, User
from backend.prompts.system_analysis import SYSTEM_ANALYSIS_PROMPT
from backend.services.extractor import extract_text
from backend.services.delta_service import run_delta
from backend.services.email_service import send_analysis_complete_email, send_analysis_failed_email
from backend.services.storage_service import StorageService
from backend.services.analytics_service import ph

logger = logging.getLogger(__name__)

# Client OpenAI (synchrone - suffisant pour un background task)
_client = OpenAI(api_key=settings.openai_api_key)


def call_gpt4o(text: str, company_name: str, sector: str) -> dict:
    """
    Envoie le texte extrait à GPT-4o et retourne le JSON structuré.

    Raises:
        RuntimeError: si l'appel API échoue ou le JSON est invalide.
    """
    user_message = (
        f"Entreprise : {company_name}\n"
        f"Secteur : {sector or 'Non précisé'}\n\n"
        f"Rapport :\n{text}"
    )

    try:
        response = _client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_ANALYSIS_PROMPT},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=4000,
        )
        raw_content = response.choices[0].message.content
        return json.loads(raw_content)

    except json.JSONDecodeError as exc:
        logger.error("JSON invalide retourné par GPT-4o : %s", exc)
        raise RuntimeError(f"GPT-4o a retourné un JSON invalide : {exc}") from exc
    except Exception as exc:
        logger.error("Erreur appel GPT-4o : %s", exc)
        raise RuntimeError(f"Erreur appel GPT-4o : {exc}") from exc


def _save_results(analysis: Analysis, result: dict, raw_json: str) -> None:
    """Mappe le dict GPT-4o vers les colonnes du modèle Analysis."""
    scores = result.get("scores", {})
    analysis.score_env = scores.get("environment")
    analysis.score_social = scores.get("social")
    analysis.score_gov = scores.get("governance")
    analysis.score_global = scores.get("global")

    csrd = result.get("csrd_compliance", {})
    analysis.csrd_ready = csrd.get("csrd_ready")
    analysis.csrd_coverage_pct = csrd.get("coverage_percentage")
    analysis.missing_disclosures = json.dumps(csrd.get("missing_disclosures", []), ensure_ascii=False)

    analysis.kpis_detected = json.dumps(result.get("kpis", []), ensure_ascii=False)
    analysis.strengths = json.dumps(result.get("strengths", []), ensure_ascii=False)
    analysis.weaknesses = json.dumps(result.get("weaknesses", []), ensure_ascii=False)
    analysis.recommendations = json.dumps(result.get("recommendations", []), ensure_ascii=False)
    analysis.esrs_coverage = json.dumps(result.get("esrs_coverage", {}), ensure_ascii=False)
    analysis.executive_summary = result.get("executive_summary")
    analysis.raw_llm_response = raw_json


def run_analysis_pipeline(analysis_id: int, storage_key: str, db: Session) -> None:
    """
    Pipeline complet exécuté en background task :
    1. Charge l'analyse depuis la DB
    2. Télécharge le fichier depuis R2 (ou chemin local en dev)
    3. Extrait le texte du document
    4. Appelle GPT-4o
    5. Sauvegarde les résultats
    6. Supprime le fichier du stockage

    Met à jour le status en 'success' ou 'failed' dans tous les cas.
    """
    start = time.time()
    local_path: str | None = None  # chemin du fichier téléchargé localement

    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        logger.error("Analysis ID %d introuvable en DB", analysis_id)
        return

    # Récupérer le nom de l'entreprise et le secteur
    company = db.query(Company).filter(Company.id == analysis.company_id).first()
    company_name = company.name if company else "Inconnue"
    sector = company.sector if company else ""

    try:
        # Passer en "processing"
        analysis.status = "processing"
        db.commit()

        # 1. Récupérer le fichier depuis le stockage (R2 -> tempfile local, ou direct si local)
        logger.info("Pipeline [%d] - Récupération fichier : %s", analysis_id, storage_key)
        local_path = StorageService.download_to_tempfile(storage_key)

        # 2. Extraction du texte
        logger.info("Pipeline [%d] - Extraction texte : %s", analysis_id, analysis.source_filename)
        text = extract_text(local_path, analysis.source_format)

        if not text.strip():
            raise RuntimeError("Le document ne contient aucun texte exploitable.")

        # 2. Appel GPT-4o
        logger.info("Pipeline [%d] - Appel GPT-4o (%d caractères)", analysis_id, len(text))
        result = call_gpt4o(text, company_name, sector)
        raw_json = json.dumps(result, ensure_ascii=False)

        # 3. Sauvegarde des résultats
        _save_results(analysis, result, raw_json)
        analysis.status = "success"
        analysis.processing_time_s = round(time.time() - start, 2)
        db.commit()

        logger.info(
            "Pipeline [%d] - Succès en %.1fs (score global: %s)",
            analysis_id, analysis.processing_time_s, analysis.score_global,
        )

        # PostHog : analyse terminée avec succès
        user_obj = db.query(User).filter(User.id == analysis.user_id).first()
        ph.capture(analysis.user_id, "analysis_completed", {
            "analysis_id": analysis_id,
            "score_env": analysis.score_env,
            "score_social": analysis.score_social,
            "score_gov": analysis.score_gov,
            "score_global": analysis.score_global,
            "csrd_ready": analysis.csrd_ready,
            "csrd_coverage_pct": analysis.csrd_coverage_pct,
            "processing_time_s": analysis.processing_time_s,
            "format": analysis.source_format,
            "plan": user_obj.plan if user_obj else "unknown",
        })

        # 4. Delta Report (si analyse précédente existe)
        try:
            delta_result = run_delta(analysis, db)
            if delta_result:
                logger.info("Pipeline [%d] - Delta calculé avec succès", analysis_id)
        except Exception as delta_exc:
            # Le delta est optionnel - on ne fait pas échouer l'analyse principale
            logger.warning("Pipeline [%d] - Delta échoué (non bloquant) : %s", analysis_id, delta_exc)

        # 5. Email de notification (succès - si opt-in)
        try:
            user = db.query(User).filter(User.id == analysis.user_id).first()
            if user and user.email_notifications:
                send_analysis_complete_email(
                    email=user.email,
                    analysis_id=analysis.id,
                    company_name=company_name,
                    score_global=analysis.score_global or 0,
                    csrd_ready=analysis.csrd_ready or False,
                    report_year=analysis.report_year,
                )
        except Exception as email_exc:
            logger.warning("Pipeline [%d] - Email succès non envoyé : %s", analysis_id, email_exc)

    except Exception as exc:
        analysis.status = "failed"
        analysis.error_message = str(exc)[:500]
        analysis.processing_time_s = round(time.time() - start, 2)
        logger.error("Pipeline [%d] - Échec : %s", analysis_id, exc)

        # PostHog : analyse échouée (signal pour debugger les cas d'erreur)
        ph.capture(analysis.user_id, "analysis_failed", {
            "analysis_id": analysis_id,
            "error": str(exc)[:200],
            "format": analysis.source_format,
            "processing_time_s": analysis.processing_time_s,
        })

        # Email de notification (échec)
        try:
            user = db.query(User).filter(User.id == analysis.user_id).first()
            if user:
                send_analysis_failed_email(
                    email=user.email,
                    analysis_id=analysis.id,
                    company_name=company_name,
                    error_message=str(exc)[:200],
                )
        except Exception as email_exc:
            logger.warning("Pipeline [%d] - Email échec non envoyé : %s", analysis_id, email_exc)

    finally:
        db.commit()

        # Nettoyage : supprimer le fichier du stockage R2 + le tempfile local éventuel
        try:
            StorageService.delete(storage_key)
        except Exception as del_exc:
            logger.warning("Pipeline [%d] - Impossible de supprimer storage_key=%s : %s", analysis_id, storage_key, del_exc)

        if local_path and local_path != storage_key:
            # local_path est un fichier téléchargé depuis R2 (distinct de storage_key)
            try:
                Path(local_path).unlink(missing_ok=True)
            except OSError:
                pass
