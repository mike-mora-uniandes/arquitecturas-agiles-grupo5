#!/bin/sh
# Construye la imagen general Flask/Python (solventa/security-flask-base)
# que heredan todos los microservicios de este experimento, y luego levanta
# el stack.
#
# Uso:
#   sh build-base.sh            # construye base + docker compose up -d --build
#   sh build-base.sh --no-up    # solo construye la imagen base
set -e

cd "$(dirname "$0")"

if [ ! -f .env ]; then
  echo ">> Creando .env desde .env.example"
  cp .env.example .env
fi

echo ">> Construyendo solventa/security-flask-base:latest ..."
docker build -t solventa/security-flask-base:latest ./base-image

if [ "$1" = "--no-up" ]; then
  echo ">> Imagen base construida. Fin."
  exit 0
fi

echo ">> Levantando el stack ..."
docker compose up -d --build

echo ">> Estado:"
docker compose ps
