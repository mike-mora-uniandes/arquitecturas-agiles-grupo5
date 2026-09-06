#!/bin/sh
set -e

# API HTTP del microservicio. El worker de Celery / publicador al broker se
# añadirá aquí cuando exista la lógica del servicio.
exec gunicorn --bind 0.0.0.0:5000 --workers 1 --access-logfile - "app:app"
