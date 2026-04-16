"""
ESG Optimizer MVP — Point d'entrée FastAPI.
Lancer avec : uvicorn main:app --reload --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.database import create_tables

from backend.routers.auth import router as auth_router
from backend.routers.analysis import router as analysis_router
# ──────────────────────────────────────────────
# Lifespan : crée les tables au démarrage
# ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


# ──────────────────────────────────────────────
# App FastAPI
# ──────────────────────────────────────────────
app = FastAPI(
    title="ESG Optimizer API",
    description="Agent autonome de reporting ESG — Analyse CSRD/ESRS automatisée",
    version="0.1.0",
    lifespan=lifespan,
)

# ──────────────────────────────────────────────
# CORS
# ──────────────────────────────────────────────
_allowed_origins = ["http://localhost:8501"]  # Streamlit dev
if not settings.is_dev:
    # En production, ajouter l'URL réelle du frontend
    _allowed_origins = ["*"]  # à restreindre après déploiement

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(analysis_router)

# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "app": "ESG Optimizer API",
        "version": "0.1.0",
        "status": "running",
        "environment": settings.environment,
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
