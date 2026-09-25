#!/bin/sh
set -e

# Sin Celery: MS Cliente no publica ni consume del Event Bus, solo hace
# llamadas HTTP síncronas hacia MS Identidad y MS Riesgo. Instrumentado con
# OTel (único de los dos servicios de este PR que lo requiere, ver
# diseño del experimento).
exec opentelemetry-instrument gunicorn --bind 0.0.0.0:5000 --workers 1 --access-logfile - "app:app"
