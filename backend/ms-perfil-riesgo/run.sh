#!/bin/sh
set -e

# Prepara el esquema local (modelo de escritura del microservicio).
python build_database.py

# API HTTP del microservicio.
# El worker de Celery se añadirá aquí cuando exista la lógica de evaluación:
#   celery -A tareas.evaluacion worker --loglevel="${LOG_LEVEL:-info}" &
exec gunicorn --bind 0.0.0.0:5000 --workers 1 --access-logfile - "app:app"
