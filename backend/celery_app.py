"""
ESG Optimizer - Configuration Celery.

Broker + backend : Upstash Redis (TLS obligatoire avec rediss://).
En dev sans Redis, ce module est importé mais les taches tombent
en mode eager si CELERY_TASK_ALWAYS_EAGER=1, ou sont remplacees
par BackgroundTasks FastAPI (voir analysis.py).
"""

from celery import Celery
from backend.config import settings

celery_app = Celery(
    "esg_optimizer",
    broker=settings.redis_url or "redis://localhost:6379/0",
    backend=settings.redis_url or "redis://localhost:6379/0",
    include=["backend.tasks.analysis_task"],
)

celery_app.conf.update(
    # Serialisation
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Suivi des taches
    task_track_started=True,
    task_acks_late=True,

    # 1 tache a la fois par worker (analyse GPT-4o = 60-120s, gourmande en RAM)
    worker_prefetch_multiplier=1,

    # Timeout : 5 min soft (log warning), 6 min hard (SIGKILL)
    task_soft_time_limit=300,
    task_time_limit=360,

    # Expiration des resultats Redis apres 24h
    result_expires=86400,

    # Upstash Redis requiert SSL (rediss://)
    broker_use_ssl=settings.redis_url.startswith("rediss://") if settings.redis_url else False,
    redis_backend_use_ssl=settings.redis_url.startswith("rediss://") if settings.redis_url else False,
)