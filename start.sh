#!/usr/bin/env bash
# ================================================================
#  ESG Optimizer MVP — Script de demarrage production
# ----------------------------------------------------------------
#  Deux modes, controles par ENABLE_CELERY :
#
#  ENABLE_CELERY=false (defaut) — mode Streamlit (actuel)
#    1. FastAPI   (uvicorn)   sur PORT_API       (8000)
#    2. Streamlit             sur STREAMLIT_PORT (8502)
#    3. nginx route : /stripe/webhook → FastAPI, reste → Streamlit
#
#  ENABLE_CELERY=true — mode Next.js + Celery (apres migration Vercel)
#    1. FastAPI   (uvicorn)   sur PORT_API       (8000)
#    2. Celery worker         (background, sans port)
#    3. nginx route : tout → FastAPI (Next.js est sur Vercel)
#
#  Bascule : definir ENABLE_CELERY=true dans Railway Variables
#            en meme temps que tu actives le front Next.js sur Vercel.
# ================================================================

set -eu

NGINX_PORT="${PORT:-8080}"
PORT_API="${PORT_API:-8000}"
STREAMLIT_PORT=8502
ENABLE_CELERY="${ENABLE_CELERY:-false}"

echo "================================================================"
echo " ESG Optimizer — Boot"
echo "   Environment   : ${ENVIRONMENT:-production}"
echo "   PORT nginx     : ${NGINX_PORT}"
echo "   PORT FastAPI   : ${PORT_API}"
echo "   Mode Celery    : ${ENABLE_CELERY}"
echo "================================================================"

# --- Prepare les dossiers -----------------------------------------
mkdir -p /app/data /app/uploads

# --- Lance FastAPI en arriere-plan --------------------------------
PYTHONPATH=/app uvicorn backend.main:app \
    --host 0.0.0.0 \
    --port "${PORT_API}" \
    --workers "${API_WORKERS:-2}" \
    --log-level "${LOG_LEVEL:-info}" \
    --proxy-headers \
    --forwarded-allow-ips='*' &
API_PID=$!
echo "  -> FastAPI demarre (pid=${API_PID})"

# --- Attend que FastAPI soit pret (max 30s) ----------------------
for i in $(seq 1 30); do
    if curl -sf "http://localhost:${PORT_API}/health" >/dev/null 2>&1; then
        echo "  -> FastAPI healthy"
        break
    fi
    sleep 1
done

# --- Mode selon ENABLE_CELERY ------------------------------------
if [ "${ENABLE_CELERY}" = "true" ]; then

    # Mode Next.js + Celery : le frontend tourne sur Vercel
    # Le worker Celery traite les analyses GPT-4o en arriere-plan
    echo "  -> Mode Celery active"
    PYTHONPATH=/app celery \
        -A backend.celery_app \
        worker \
        --loglevel="${LOG_LEVEL:-info}" \
        --concurrency="${CELERY_CONCURRENCY:-2}" \
        --queues=celery \
        -n "worker@%h" &
    WORKER_PID=$!
    echo "  -> Celery worker demarre (pid=${WORKER_PID})"

    # nginx route tout vers FastAPI (Next.js gere le frontend)
    cat > /etc/nginx/nginx.conf << NGINX_EOF
events {
    worker_connections 1024;
}

http {
    client_max_body_size 25m;

    server {
        listen ${NGINX_PORT};

        location / {
            proxy_pass         http://127.0.0.1:${PORT_API};
            proxy_set_header   Host              \$host;
            proxy_set_header   X-Real-IP         \$remote_addr;
            proxy_set_header   X-Forwarded-For   \$proxy_add_x_forwarded_for;
            proxy_set_header   Stripe-Signature  \$http_stripe_signature;
            proxy_read_timeout 360s;
        }
    }
}
NGINX_EOF

else

    # Mode Streamlit (defaut — front actuel)
    echo "  -> Mode Streamlit (ENABLE_CELERY=false)"
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
    echo "  -> Streamlit demarre (pid=${STREAMLIT_PID}) sur port ${STREAMLIT_PORT}"

    # Attend Streamlit
    for i in $(seq 1 30); do
        if curl -sf "http://localhost:${STREAMLIT_PORT}/_stcore/health" >/dev/null 2>&1; then
            echo "  -> Streamlit healthy"
            break
        fi
        sleep 1
    done

    # nginx route /stripe/webhook → FastAPI, reste → Streamlit
    cat > /etc/nginx/nginx.conf << NGINX_EOF
events {
    worker_connections 1024;
}

http {
    client_max_body_size 25m;

    map \$http_upgrade \$connection_upgrade {
        default upgrade;
        ''      close;
    }

    server {
        listen ${NGINX_PORT};

        location = /stripe/webhook {
            proxy_pass         http://127.0.0.1:${PORT_API};
            proxy_set_header   Host              \$host;
            proxy_set_header   X-Real-IP         \$remote_addr;
            proxy_set_header   X-Forwarded-For   \$proxy_add_x_forwarded_for;
            proxy_set_header   Stripe-Signature  \$http_stripe_signature;
            proxy_read_timeout 30s;
        }

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

fi

echo "  -> Config nginx generee (port public ${NGINX_PORT})"

# --- Lance nginx au premier plan (PID 1 → Railway surveille) ----
exec nginx -g 'daemon off;'
