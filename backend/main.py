"""
ESG Optimizer - Point d'entrée FastAPI.
Lancer avec : uvicorn backend.main:app --reload --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.config import settings, APP_URL
from backend.database import create_tables

from backend.routers.auth import router as auth_router
from backend.routers.analysis import router as analysis_router
from backend.routers.history import router as history_router
from backend.routers.public import router as public_router, claim_router
from backend.routers.stripe import router as stripe_router
from backend.routers.email import router as email_router

# --- Logging ------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO if not settings.is_dev else logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("esg-optimizer")


# --- Sentry -------------------------------------------------------------
# On initialise AVANT la création de l'app FastAPI pour que l'intégration
# auto-wrap tous les handlers et capture les exceptions non gérées.
if settings.sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        release=f"esg-optimizer@{__import__('backend.config', fromlist=['APP_VERSION']).APP_VERSION}",
        traces_sample_rate=0.1 if not settings.is_dev else 1.0,
        profiles_sample_rate=0.1,
        send_default_pii=False,  # RGPD : pas d'IP, pas de cookies par défaut
        integrations=[
            StarletteIntegration(transaction_style="endpoint"),
            FastApiIntegration(transaction_style="endpoint"),
        ],
    )
    logger.info("Sentry initialisé (env=%s)", settings.environment)
else:
    logger.info("Sentry désactivé (SENTRY_DSN vide)")


# --- Lifespan -----------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    logger.info("Base de données prête - API démarrée")
    yield
    logger.info("API stoppée proprement")


# --- App FastAPI --------------------------------------------------------
app = FastAPI(
    title="ESG Optimizer API",
    description="Agent autonome de reporting ESG - Analyse CSRD/ESRS automatisée",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
# On autorise systématiquement les domaines connus (dev local, domaine de prod,
# déploiements Vercel) afin que le frontend Next.js puisse appeler l'API quel
# que soit l'environnement. Des origines supplémentaires peuvent être ajoutées
# via la variable EXTRA_CORS_ORIGINS (valeurs séparées par des virgules).
_allowed_origins = [
    "http://localhost:3000",
    "http://localhost:8501",
    "https://esg-optimizer.fr",
    "https://www.esg-optimizer.fr",
    "https://esg-optimizer.vercel.app",
    APP_URL,
]
if settings.extra_cors_origins:
    _allowed_origins += [
        origin.strip()
        for origin in settings.extra_cors_origins.split(",")
        if origin.strip()
    ]
_allowed_origins = sorted({origin for origin in _allowed_origins if origin})

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    # Couvre les URL de prévisualisation Vercel (deploy previews).
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Error handlers globaux --------------------------------------------
# Messages user-friendly en français, pas de stack trace exposée en prod.

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Gère les erreurs HTTP classiques (404, 401, 403, 429...)."""
    user_messages = {
        400: "Requête invalide. Vérifiez les données envoyées.",
        401: "Authentification requise. Connectez-vous à votre compte.",
        403: "Accès refusé. Votre plan actuel ne couvre pas cette action.",
        404: "Ressource introuvable.",
        413: "Fichier trop volumineux. Taille maximale : 20 Mo.",
        422: "Données invalides. Vérifiez le format des champs.",
        429: "Trop de requêtes. Merci de patienter quelques minutes.",
    }
    message = user_messages.get(exc.status_code, str(exc.detail))
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": message, "code": exc.status_code, "path": str(request.url.path)},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Validation Pydantic : message clair côté front."""
    first_error = exc.errors()[0] if exc.errors() else {}
    loc = " -> ".join(str(x) for x in first_error.get("loc", []) if x != "body")
    msg = first_error.get("msg", "Champ invalide")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": f"Champ « {loc} » : {msg}" if loc else "Données invalides.",
            "code": 422,
            "details": exc.errors() if settings.is_dev else None,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Dernier rempart : n'expose jamais le détail en prod, logge tout."""
    logger.exception("Unhandled exception on %s", request.url.path)
    # Sentry capture automatiquement via son intégration FastAPI
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": (
                "Une erreur interne est survenue. Notre équipe a été notifiée "
                "et travaille à résoudre le problème. Réessayez dans quelques minutes."
            ),
            "code": 500,
            "support": "hello@esg-optimizer.fr",
        },
    )


# --- Routers ------------------------------------------------------------
app.include_router(auth_router)
app.include_router(analysis_router)
app.include_router(history_router)
app.include_router(public_router)
app.include_router(claim_router)
app.include_router(stripe_router)
app.include_router(email_router)


# --- Routes racine ------------------------------------------------------
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
    """Endpoint utilisé par Railway pour le health check."""
    return {"status": "ok"}


# --- SEO : robots.txt & sitemap.xml ------------------------------------
ROBOTS_TXT = f"""User-agent: *
Allow: /
Disallow: /api/
Disallow: /auth/
Disallow: /docs
Disallow: /redoc
Disallow: /openapi.json

Sitemap: {APP_URL}/sitemap.xml
"""

SITEMAP_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>{APP_URL}/</loc>
        <changefreq>weekly</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>{APP_URL}/tarifs</loc>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>{APP_URL}/mentions</loc>
        <changefreq>yearly</changefreq>
        <priority>0.4</priority>
    </url>
    <url>
        <loc>{APP_URL}/blog/guide-csrd-2026-pme</loc>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>{APP_URL}/blog/10-erreurs-reporting-esg</loc>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>{APP_URL}/blog/esrs-e1-e5-expliques</loc>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
</urlset>
"""


@app.get("/robots.txt", include_in_schema=False)
async def robots():
    return PlainTextResponse(ROBOTS_TXT, media_type="text/plain")


@app.get("/sitemap.xml", include_in_schema=False)
async def sitemap():
    return Response(content=SITEMAP_XML, media_type="application/xml")


# --- Debug Sentry (utile pour tester l'intégration, à désactiver en prod)
if settings.is_dev:
    @app.get("/debug/sentry", include_in_schema=False)
    async def trigger_error():
        _ = 1 / 0  # déclenche ZeroDivisionError -> doit apparaître dans Sentry
        return {"ok": True}
