#!/usr/bin/env bash
# ================================================================
#  ESG Optimizer MVP — Script de démarrage production
# ----------------------------------------------------------------
#  Ordre de démarrage :
#    1. FastAPI   (uvicorn)   sur $PORT_API       (8000, interne)
#    2. Streamlit             sur $STREAMLIT_PORT (8501, interne)
#    3. nginx     (proxy)     sur $PORT           (public Railway)
#
#  nginx route :
#    /stripe/webhook  →  FastAPI  (8000)
#    tout le reste    →  Streamlit (8501)
# ================================================================

set -eu

NGINX_PORT="${PORT:-8080}"
PORT_API="${PORT_API:-8000}"
STREAMLIT_PORT=8502   # Port interne fixe — jamais écrasé par Railway

echo "================================================================"
echo " ESG Optimizer — Boot"
echo "   Environment   : ${ENVIRONMENT:-production}"
echo "   PORT nginx     : ${NGINX_PORT}"
echo "   PORT FastAPI   : ${PORT_API}"
echo "   PORT Streamlit : ${STREAMLIT_PORT}"
echo "================================================================"

# --- Prépare les dossiers -----------------------------------------
mkdir -p /app/data /app/uploads

# --- Lance le backend FastAPI en arrière-plan --------------------
uvicorn backend.main:app \
    --host 0.0.0.0 \
    --port "${PORT_API}" \
    --workers "${API_WORKERS:-2}" \
    --log-level "${LOG_LEVEL:-info}" \
    --proxy-headers \
    --forwarded-allow-ips='*' &
API_PID=$!
echo "  → FastAPI démarré (pid=${API_PID})"

# --- Attend que FastAPI soit prêt (max 30s) ----------------------
for i in $(seq 1 30); do
    if curl -sf "http://localhost:${PORT_API}/health" >/dev/null 2>&1; then
        echo "  → FastAPI healthy"
        break
    fi
    sleep 1
done

# --- Lance Streamlit en arrière-plan (port interne) --------------
streamlit run frontend/app.py \
    --server.port "${STREAMLIT_PORT}" \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false \
    --server.enableCORS false \
    --server.enableXsrfProtection true \
    --theme.primaryColor "#1A3D22" \
    --theme.backgroundColor "#F5F2EC" \
    --theme.secondaryBackgroundColor "#FFFFFF" \
    --theme.textColor "#1A3D22" &
STREAMLIT_PID=$!
echo "  → Streamlit démarré (pid=${STREAMLIT_PID}) sur port ${STREAMLIT_PORT}"

# --- Attend que Streamlit soit prêt (max 30s) --------------------
for i in $(seq 1 30); do
    if curl -sf "http://localhost:${STREAMLIT_PORT}/_stcore/health" >/dev/null 2>&1; then
        echo "  → Streamlit healthy"
        break
    fi
    sleep 1
done

# --- Génère la config nginx dynamiquement ------------------------
cat > /etc/nginx/nginx.conf << NGINX_EOF
events {
    worker_connections 1024;
}

http {
    map \$http_upgrade \$connection_upgrade {
        default upgrade;
        ''      close;
    }

    server {
        listen ${NGINX_PORT};

        # Stripe webhook → FastAPI
        location = /stripe/webhook {
            proxy_pass         http://127.0.0.1:${PORT_API};
            proxy_set_header   Host              \$host;
            proxy_set_header   X-Real-IP         \$remote_addr;
            proxy_set_header   X-Forwarded-For   \$proxy_add_x_forwarded_for;
            proxy_set_header   Stripe-Signature  \$http_stripe_signature;
            proxy_read_timeout 30s;
        }

        # Tout le reste → Streamlit
        location / {
            proxy_pass         http://127.0.0.1:${STREAMLIT_PORT};
            proxy_http_version 1.1;
            proxy_set_header   Upgrade    \$http_upgrade;
            proxy_set_header   Connection \$connection_upgrade;
            proxy_set_header   Host       \$host;
            proxy_set_header   X-Real-IP  \$remote_addr;
            proxy_read_timeout 86400s;
        }
    }
}
NGINX_EOF

echo "  → Config nginx générée (port public ${NGINX_PORT})"

# --- Lance nginx au premier plan (PID 1 → Railway surveille) ----
exec nginx -g 'daemon off;'
