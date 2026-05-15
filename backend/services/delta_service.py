"""
ESG Optimizer MVP - Service Delta (comparaison N vs N-1).
Calcule les écarts de scores, compare les couvertures ESRS,
et appelle GPT-4o pour générer la narration comparative.
"""

import json
import logging

from openai import OpenAI
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models import Analysis, Company
from backend.prompts.system_delta import SYSTEM_DELTA_PROMPT
from backend.utils import safe_json_loads

logger = logging.getLogger(__name__)

_client = OpenAI(api_key=settings.openai_api_key)


def find_previous_analysis(db: Session, analysis: Analysis) -> Analysis | None:
    """
    Cherche l'analyse précédente de la même entreprise.
    Critères : même company_id, status='success', report_year < année courante,
    ordonnée par report_year DESC puis created_at DESC.
    """
    query = (
        db.query(Analysis)
        .filter(
            Analysis.company_id == analysis.company_id,
            Analysis.id != analysis.id,
            Analysis.status == "success",
        )
    )

    # Toute analyse créée avant celle-ci (même année acceptée),
    # ordonnée par report_year desc puis created_at desc -> la plus récente/pertinente en premier.
    return (
        query
        .filter(Analysis.created_at < analysis.created_at)
        .order_by(Analysis.report_year.desc(), Analysis.created_at.desc())
        .first()
    )


# _safe_json_loads migré vers backend.utils.safe_json_loads
_safe_json_loads = safe_json_loads  # alias rétro-compat


def compute_score_deltas(current: Analysis, previous: Analysis) -> dict:
    """Calcule les différences de scores brutes."""
    deltas = {}
    for field in ("score_env", "score_social", "score_gov", "score_global"):
        curr_val = getattr(current, field)
        prev_val = getattr(previous, field)
        if curr_val is not None and prev_val is not None:
            deltas[field] = round(curr_val - prev_val, 1)
        else:
            deltas[field] = None
    return deltas


def _build_comparison_payload(current: Analysis, previous: Analysis, company_name: str) -> str:
    """
    Construit le message user envoyé à GPT-4o avec les données des deux analyses.
    """
    def _format_analysis(a: Analysis, label: str) -> str:
        return (
            f"--- {label} (année {a.report_year or 'N/A'}) ---\n"
            f"Score Environnement : {a.score_env}\n"
            f"Score Social : {a.score_social}\n"
            f"Score Gouvernance : {a.score_gov}\n"
            f"Score Global : {a.score_global}\n"
            f"CSRD Ready : {a.csrd_ready}\n"
            f"Couverture CSRD : {a.csrd_coverage_pct}%\n"
            f"Couverture ESRS : {_safe_json_loads(a.esrs_coverage) or {}}\n"
            f"KPIs : {_safe_json_loads(a.kpis_detected) or []}\n"
            f"Résumé : {a.executive_summary or 'N/A'}\n"
            f"Points forts : {_safe_json_loads(a.strengths) or []}\n"
            f"Lacunes : {_safe_json_loads(a.weaknesses) or []}\n"
        )

    payload = (
        f"Entreprise : {company_name}\n\n"
        f"{_format_analysis(previous, 'ANALYSE N-1')}\n"
        f"{_format_analysis(current, 'ANALYSE N (actuelle)')}\n"
    )
    return payload


def call_gpt4o_delta(current: Analysis, previous: Analysis, company_name: str) -> dict:
    """
    Appelle GPT-4o avec le prompt delta pour générer la narration comparative.
    Retourne le JSON structuré.
    """
    user_message = _build_comparison_payload(current, previous, company_name)

    try:
        response = _client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_DELTA_PROMPT},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=4000,
        )
        raw_content = response.choices[0].message.content
        return json.loads(raw_content)

    except json.JSONDecodeError as exc:
        logger.error("JSON invalide retourné par GPT-4o (delta) : %s", exc)
        raise RuntimeError(f"GPT-4o delta - JSON invalide : {exc}") from exc
    except Exception as exc:
        logger.error("Erreur appel GPT-4o (delta) : %s", exc)
        raise RuntimeError(f"Erreur appel GPT-4o delta : {exc}") from exc


def run_delta(analysis: Analysis, db: Session) -> dict | None:
    """
    Point d'entrée principal du service delta.
    1. Cherche l'analyse précédente
    2. Calcule les deltas de scores
    3. Appelle GPT-4o pour la narration
    4. Sauvegarde dans l'analyse courante

    Retourne le dict delta complet ou None si pas d'analyse précédente.
    """
    previous = find_previous_analysis(db, analysis)
    if previous is None:
        logger.info("Delta [%d] - Aucune analyse précédente trouvée, skip.", analysis.id)
        return None

    logger.info(
        "Delta [%d] - Comparaison avec analyse [%d] (année %s vs %s)",
        analysis.id, previous.id, previous.report_year, analysis.report_year,
    )

    # 1. Calcul des deltas de scores
    score_deltas = compute_score_deltas(analysis, previous)
    analysis.delta_env = score_deltas["score_env"]
    analysis.delta_social = score_deltas["score_social"]
    analysis.delta_gov = score_deltas["score_gov"]
    analysis.delta_global = score_deltas["score_global"]

    # 2. Narration GPT-4o
    company = db.query(Company).filter(Company.id == analysis.company_id).first()
    company_name = company.name if company else "Inconnue"

    delta_result = call_gpt4o_delta(analysis, previous, company_name)
    analysis.delta_narrative = json.dumps(delta_result, ensure_ascii=False)

    db.commit()

    logger.info(
        "Delta [%d] - Terminé. Deltas: E=%s, S=%s, G=%s, Global=%s",
        analysis.id, analysis.delta_env, analysis.delta_social,
        analysis.delta_gov, analysis.delta_global,
    )

    return delta_result
