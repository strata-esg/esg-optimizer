# ================================================================
#  ESG Optimizer MVP — Dockerfile multi-process
# ----------------------------------------------------------------
#  Lance en parallèle :
#    - nginx      (reverse proxy) sur $PORT   (exposé par Railway)
#    - uvicorn    (FastAPI)        sur $PORT_API (8000, interne)
#    - streamlit  (Frontend)       sur 8501     (interne)
#
#  nginx route :
#    POST /stripe/webhook  →  FastAPI (8000)
#    tout le reste         →  Streamlit (8501)
#
#  Build local :
#     docker build -t esg-optimizer .
#  Run local :
#     docker run -p 8080:8080 --env-file .env esg-optimizer
# ================================================================

FROM python:3.11-slim AS base

# Variables d'env Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Dépendances système (pour PyMuPDF, reportlab, matplotlib, psycopg2, nginx)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libfreetype6-dev \
        libjpeg-dev \
        zlib1g-dev \
        libxml2-dev \
        libxslt1-dev \
        curl \
        nginx \
        gettext-base \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --- Dépendances Python -----------------------------------------
COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# --- Code applicatif --------------------------------------------
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY blog/ ./blog/
COPY data/ ./data/
COPY frontend/.streamlit/ ./.streamlit/

# Dossier pour la base SQLite + uploads persistants (monté en volume Railway)
RUN mkdir -p /app/data /app/uploads

# --- Script de démarrage multi-process --------------------------
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Ports par défaut (Railway écrase $PORT automatiquement)
# nginx écoute sur $PORT (public), FastAPI sur $PORT_API (interne), Streamlit sur 8501 (interne)
ENV PORT=8080 \
    PORT_API=8000 \
    STREAMLIT_PORT=8501 \
    API_BASE_URL=http://localhost:8000

EXPOSE 8080

# Healthcheck : Railway attend un 200 sur $PORT (nginx proxie vers Streamlit)
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:${PORT}/_stcore/health || exit 1

CMD ["/app/start.sh"]
