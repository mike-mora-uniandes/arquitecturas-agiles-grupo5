#!/bin/sh
# Arranca Redis y, en cuanto responde, precarga el seed de perfiles de prueba
# de ASR2 (backend/redis/seed/profiles.redis). El caché es efímero: se repuebla
# en cada arranque del contenedor, sin servicios ni jobs externos.
set -eu

REDIS_CONF="/usr/local/etc/redis/redis.conf"
SEED_FILE="${REDIS_SEED_FILE:-/usr/local/etc/redis/seed/profiles.redis}"

redis-server "$REDIS_CONF" &
REDIS_PID="$!"

trap 'kill -TERM "$REDIS_PID" 2>/dev/null || true' TERM INT

# Espera activa a que el servidor acepte conexiones antes de cargar el seed.
until redis-cli ping 2>/dev/null | grep -q PONG; do
  sleep 0.2
done

if [ -f "$SEED_FILE" ]; then
  redis-cli < "$SEED_FILE" >/dev/null
  echo "redis: seed cargado desde $SEED_FILE"
else
  echo "redis: sin seed ($SEED_FILE no existe)"
fi

# Cede el PID 1 a redis-server para el resto de la vida del contenedor.
wait "$REDIS_PID"
