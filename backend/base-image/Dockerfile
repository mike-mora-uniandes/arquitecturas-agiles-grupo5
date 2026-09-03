# Imagen general Flask/Python para los microservicios de Solventa.
# Se construye una sola vez con backend/build-base.sh y la heredan los MS:
#   FROM solventa/flask-base:latest
# Python 3.12 (no 3.13): es el rango probado por celery 5.4.x.
FROM python:3.12-slim

# No generar .pyc y logs sin buffer (salida inmediata en docker logs).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /backend

COPY requirements-base.txt .
RUN pip install --no-cache-dir -r requirements-base.txt
