# Imagen Redis de Solventa: caché de datos externos usada por MS PerfilRiesgo
# para la táctica de Exception Handling (ASR2).
#
# El entrypoint arranca Redis y precarga seed/profiles.redis en cada arranque;
# no hace falta el servicio 'redis-seed' ni ningún job externo.
FROM redis:7-alpine

COPY redis.conf /usr/local/etc/redis/redis.conf
COPY seed/profiles.redis /usr/local/etc/redis/seed/profiles.redis
COPY entrypoint.sh /usr/local/bin/solventa-redis-entrypoint.sh

RUN chmod +x /usr/local/bin/solventa-redis-entrypoint.sh

# Reemplaza por completo el entrypoint/cmd de la imagen base.
ENTRYPOINT ["/usr/local/bin/solventa-redis-entrypoint.sh"]
CMD []
