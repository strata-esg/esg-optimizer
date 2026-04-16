"""
ESG Optimizer MVP — Service d'analyse GPT-4o.
Orchestre : extraction texte → appel LLM → parsing JSON → sauvegarde DB.
"""

import json
import logging
import time
from pathlib import Path

from openai import OpenAI
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models import Analysis, Company
from backend.prompts.system_analysis import SYSTEM_ANALYSIS_PROMPT
from backend.services.extractor import extract_text

logger = logging.getLogger(__name__)

# Client OpenAI (synchrone — suffisant pour un background task)
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


def run_analysis_pipeline(analysis_id: int, file_path: str, db: Session) -> None:
    """
    Pipeline complet exécuté en background task :
    1. Charge l'analyse depuis la DB
    2. Extrait le texte du document
    3. Appelle GPT-4o
    4. Sauvegarde les résultats
    5. Supprime le fichier temporaire

    Met à jour le status en 'success' ou 'failed' dans tous les cas.
    """
    start = time.time()

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

        # 1. Extraction du texte
        logger.info("Pipeline [%d] — Extraction texte : %s", analysis_id, analysis.source_filename)
        text = extract_text(file_path, analysis.source_format)

        if not text.strip():
            raise RuntimeError("Le document ne contient aucun texte exploitable.")

        # 2. Appel GPT-4o
        logger.info("Pipeline [%d] — Appel GPT-4o (%d caractères)", analysis_id, len(text))
        result = call_gpt4o(text, company_name, sector)
        raw_json = json.dumps(result, ensure_ascii=False)

        # 3. Sauvegarde des résultats
        _save_results(analysis, result, raw_json)
        analysis.status = "success"
        analysis.processing_time_s = round(time.time() - start, 2)

        logger.info(
            "Pipeline [%d] — Succès en %.1fs (score global: %s)",
            analysis_id, analysis.processing_time_s, analysis.score_global,
        )

    except Exception as exc:
        analysis.status = "failed"
        analysis.error_message = str(exc)[:500]
        analysis.processing_time_s = round(time.time() - start, 2)
        logger.error("Pipeline [%d] — Échec : %s", analysis_id, exc)

    finally:
        db.commit()

        # Nettoyage du fichier temporaire
        try:
            Path(file_path).unlink(missing_ok=True)
        except OSError:
            pass
