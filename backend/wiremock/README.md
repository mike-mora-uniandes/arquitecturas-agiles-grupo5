# wiremock

Simula las fuentes externas Open Data / Open Finance para los 3 escenarios de
fallo del experimento (ok / timeout / error 5xx).

Hoy `docker-compose.yml` usa la imagen oficial `wiremock/wiremock:3.9.2` sin
mappings. Pendiente:

- `mappings/` con las respuestas de `/open-data` y `/open-finance`,
- `__files/` con los payloads,
- montar ambas carpetas como volumen en el servicio `wiremock` (o construir
  una imagen propia con `build: ./wiremock`).
