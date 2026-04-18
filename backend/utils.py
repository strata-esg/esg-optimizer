"""
ESG Optimizer MVP — Utilitaires partagés.
Fonctions communes utilisées dans plusieurs modules.
"""

import json


def safe_json_loads(raw: str | None) -> dict | list | None:
    """
    Parse un champ JSON stocké en string dans la DB.
    Retourne None si la valeur est None ou si le JSON est invalide.
    """
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
