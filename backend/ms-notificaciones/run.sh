#!/usr/bin/env bash
# API + worker Celery en el mismo contenedor. Si cualquiera de los dos termina,
# se tumba el contenedor para que el fallo sea visible en 'docker compose ps'.
set -euo pipefail

opentelemetry-instrument celery -A tareas.entrega:celery_app worker \
  --loglevel="${LOG_LEVEL:-info}" \
  --concurrency=1 &
worker_pid=$!

opentelemetry-instrument gunicorn \
  --bind 0.0.0.0:5000 --workers 1 --access-logfile - "app:app" &
api_pid=$!

wait -n
echo ">> Un proceso terminó; deteniendo el contenedor."
kill "$worker_pid" "$api_pid" 2>/dev/null || true
exit 1
