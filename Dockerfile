# ================================================================
#  ESG Optimizer MVP — Dockerfile multi-process (Sprint 6H)
# ----------------------------------------------------------------
#  Lance en parallèle :
#    - uvicorn  (FastAPI)   sur $PORT_API    (8000 par défaut)
#    - streamlit (Frontend) sur $PORT        (8501 par défaut, exposé par Railway)
#
#  Railway définit automatiquement la variable $PORT : on l'utilise
#  pour Streamlit (qui devient le point d'entrée web public).
#  L'API reste interne au container et est appelée par Streamlit
#  via http://localhost:$PORT_API.
#
#  Build local :
#     docker build -t esg-optimizer .
#  Run local :
#     docker run -p 8501:8501 -p 8000:8000 --env-file .env esg-optimizer
# ================================================================

FROM python:3.11-slim AS base

# Variables d'env Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Dépendances système (pour PyMuPDF, reportlab, matplotlib, psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libfreetype6-dev \
        libjpeg-dev \
        zlib1g-dev \
        libxml2-dev \
        libxslt1-dev \
        curl \
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
ENV PORT=8501 \
    PORT_API=8000 \
    API_BASE_URL=http://localhost:8000

EXPOSE 8501
EXPOSE 8000

# Healthcheck : Railway attend un 200 sur $PORT
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT}/_stcore/health || exit 1

CMD ["/app/start.sh"]
