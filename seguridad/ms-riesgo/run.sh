#!/bin/sh
set -e

# Productor puro (publica vía Celery, no consume) — solo necesita el
# proceso HTTP, sin worker de Celery corriendo.
exec gunicorn --bind 0.0.0.0:5000 --workers 1 --access-logfile - "app:app"
