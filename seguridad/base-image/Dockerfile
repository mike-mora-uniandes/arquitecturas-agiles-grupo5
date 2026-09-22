# Imagen general Flask/Python para los microservicios del experimento de
# seguridad. Se construye una sola vez con seguridad/build-base.sh y la
# heredan los MS: FROM solventa/security-flask-base:latest
#
# Imagen propia de este experimento (no reutiliza backend/base-image) para
# mantener los dos experimentos desacoplados.
FROM python:3.12-slim@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /backend

COPY requirements-base.txt .
RUN pip install --no-cache-dir -r requirements-base.txt
