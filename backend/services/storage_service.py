"""
ESG Optimizer - Service de stockage des fichiers uploadés.

En production (USE_R2_STORAGE=true) : Cloudflare R2 via API S3-compatible.
En développement (USE_R2_STORAGE=false) : tempfile local (comportement historique).

Pourquoi R2 ?
- Les volumes Railway sont éphémères : un redeploy efface les fichiers temporaires.
- Si le background task tourne après un restart, le fichier est introuvable -> échec silencieux.
- R2 : gratuit jusqu'à 10 GB, pas d'egress fees, S3-compatible avec boto3.

Usage :
    from backend.services.storage_service import StorageService
    key = StorageService.upload(content, "rapport.pdf")   # -> "uploads/uuid.pdf"
    path = StorageService.download_to_tempfile(key)       # -> "/tmp/esg_xxx.pdf"
    StorageService.delete(key)
"""

import logging
import tempfile
import uuid
from pathlib import Path

from backend.config import settings

logger = logging.getLogger(__name__)


def _get_r2_client():
    """Crée un client boto3 pointant vers Cloudflare R2 (endpoint S3-compatible)."""
    import boto3
    from botocore.config import Config

    endpoint = f"https://{settings.r2_account_id}.r2.cloudflarestorage.com"
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


class StorageService:
    """Interface unique pour le stockage des fichiers - R2 ou local selon config."""

    @staticmethod
    def upload(content: bytes, filename: str) -> str:
        """
        Stocke le contenu et retourne une clé (chemin R2 ou chemin local).

        En mode R2 : clé = "uploads/{uuid}.{ext}"
        En mode local : clé = chemin absolu du tempfile (comportement historique)
        """
        ext = Path(filename).suffix.lower().lstrip(".")
        unique_id = uuid.uuid4().hex

        if settings.use_r2_storage:
            key = f"uploads/{unique_id}.{ext}"
            try:
                client = _get_r2_client()
                content_type_map = {
                    "pdf": "application/pdf",
                    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                }
                content_type = content_type_map.get(ext, "application/octet-stream")
                client.put_object(
                    Bucket=settings.r2_bucket_name,
                    Key=key,
                    Body=content,
                    ContentType=content_type,
                )
                logger.info("StorageService - Fichier uploadé sur R2 : %s (%d octets)", key, len(content))
                return key
            except Exception as exc:
                logger.error("StorageService - Échec upload R2 (%s), fallback local : %s", key, exc)
                # En cas d'échec R2, on bascule sur local pour ne pas bloquer l'utilisateur
                return StorageService._save_local(content, ext)
        else:
            return StorageService._save_local(content, ext)

    @staticmethod
    def _save_local(content: bytes, ext: str) -> str:
        """Sauvegarde dans un fichier temporaire local et retourne son chemin."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}", prefix="esg_") as tmp:
            tmp.write(content)
            path = tmp.name
        logger.debug("StorageService - Fichier sauvegardé localement : %s", path)
        return path

    @staticmethod
    def download_to_tempfile(key: str) -> str:
        """
        Télécharge le fichier depuis R2 (ou vérifie l'existence locale) vers un tempfile.
        Retourne le chemin du fichier local prêt pour l'extraction.

        Si key est déjà un chemin absolu local (mode dev), retourne tel quel.
        """
        # Clé locale : chemin absolu existant (mode dev ou fallback)
        if key.startswith("/") or (len(key) > 1 and key[1] == ":"):
            if Path(key).exists():
                return key
            raise FileNotFoundError(f"Fichier local introuvable : {key}")

        # Clé R2 : télécharger vers un tempfile
        if settings.use_r2_storage:
            try:
                ext = Path(key).suffix  # ex: ".pdf"
                client = _get_r2_client()
                response = client.get_object(Bucket=settings.r2_bucket_name, Key=key)
                content = response["Body"].read()

                with tempfile.NamedTemporaryFile(delete=False, suffix=ext, prefix="esg_dl_") as tmp:
                    tmp.write(content)
                    local_path = tmp.name

                logger.info(
                    "StorageService - Fichier téléchargé depuis R2 : %s -> %s (%d octets)",
                    key, local_path, len(content),
                )
                return local_path
            except Exception as exc:
                logger.error("StorageService - Échec download R2 (%s) : %s", key, exc)
                raise RuntimeError(f"Impossible de récupérer le fichier depuis le stockage : {exc}") from exc
        else:
            # Clé non-absolue en mode local : c'est un bug de configuration
            raise FileNotFoundError(f"Clé de fichier non reconnue (R2 désactivé) : {key}")

    @staticmethod
    def delete(key: str) -> None:
        """
        Supprime le fichier du stockage (R2 ou local).
        Ne lève pas d'exception si le fichier est déjà absent.
        """
        # Chemin local
        if key.startswith("/") or (len(key) > 1 and key[1] == ":"):
            try:
                Path(key).unlink(missing_ok=True)
                logger.debug("StorageService - Fichier local supprimé : %s", key)
            except OSError as exc:
                logger.warning("StorageService - Impossible de supprimer %s : %s", key, exc)
            return

        # Clé R2
        if settings.use_r2_storage:
            try:
                client = _get_r2_client()
                client.delete_object(Bucket=settings.r2_bucket_name, Key=key)
                logger.info("StorageService - Fichier R2 supprimé : %s", key)
            except Exception as exc:
                logger.warning("StorageService - Impossible de supprimer R2 (%s) : %s", key, exc)
