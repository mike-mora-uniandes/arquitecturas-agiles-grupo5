# Imagen Redis de Solventa: caché de datos externos usada por MS PerfilRiesgo
# para la táctica de Exception Handling (ASR2).
FROM redis:7-alpine

COPY redis.conf /usr/local/etc/redis/redis.conf

CMD ["redis-server", "/usr/local/etc/redis/redis.conf"]
