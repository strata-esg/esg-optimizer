#!/usr/bin/env bash
# ================================================================
#  ESG Optimizer MVP — Script de démarrage production (Sprint 6H)
# ----------------------------------------------------------------
#  Lance FastAPI + Streamlit en parallèle dans le même container.
#  Si l'un des deux meurt, le container s'arrête (Railway redémarre).
# ================================================================

set -eu

echo "================================================================"
echo " ESG Optimizer — Boot"
echo "   Environment : ${ENVIRONMENT:-production}"
echo "   PORT (frontend) : ${PORT:-8501}"
echo "   PORT_API (backend) : ${PORT_API:-8000}"
echo "================================================================"

# --- Prépare la base de données -----------------------------------
mkdir -p /app/data /app/uploads

# --- Lance le backend FastAPI en arrière-plan --------------------
uvicorn backend.main:app \
    --host 0.0.0.0 \
    --port "${PORT_API:-8000}" \
    --workers "${API_WORKERS:-2}" \
    --log-level "${LOG_LEVEL:-info}" \
    --proxy-headers \
    --forwarded-allow-ips='*' &
API_PID=$!
echo "  → FastAPI démarré (pid=${API_PID})"

# --- Attend que l'API soit prête (max 30s) -----------------------
for i in $(seq 1 30); do
    if curl -sf "http://localhost:${PORT_API:-8000}/health" >/dev/null 2>&1; then
        echo "  → FastAPI healthy"
        break
    fi
    sleep 1
done

# --- Lance Streamlit au premier plan (PID 1) ---------------------
exec streamlit run frontend/app.py \
    --server.port "${PORT:-8501}" \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false \
    --server.enableCORS false \
    --server.enableXsrfProtection true \
    --theme.primaryColor "#1A3D22" \
    --theme.backgroundColor "#F5F2EC" \
    --theme.secondaryBackgroundColor "#FFFFFF" \
    --theme.textColor "#1A3D22"
