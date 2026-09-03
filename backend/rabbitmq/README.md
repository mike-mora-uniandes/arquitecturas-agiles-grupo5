# rabbitmq

**Dueño: Michael.**

Hoy `docker-compose.yml` usa la imagen oficial `rabbitmq:3.13-management-alpine`
directamente. Si necesitas colas/exchanges predefinidos, la DLQ o plugins:

1. añade aquí `Dockerfile`, `definitions.json` y/o `enabled_plugins`,
2. en `docker-compose.yml` cambia el servicio `rabbitmq` de `image:` a
   `build: ./rabbitmq`.
