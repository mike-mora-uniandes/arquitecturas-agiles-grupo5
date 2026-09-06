# redis

Imagen `solventa/redis` (base `redis:7-alpine`). Cumple dos funciones en
`ms-perfil-riesgo`:

1. **Caché de respaldo del perfil** — táctica *Exception Handling* (ASR2): cuando
   una fuente externa falla, el resultado se completa leyendo el último perfil
   válido guardado aquí, en `< 100 ms` adicionales y sin error visible.
2. **Marca de idempotencia** — evita recalcular (y re-notificar de forma
   distinta) si el broker reentrega la misma solicitud.

## Configuración (`redis.conf`)

| Ajuste | Valor | Motivo |
|---|---|---|
| `maxmemory` | `128mb` | suficiente para el set de prueba |
| `maxmemory-policy` | `noeviction` | el respaldo no debe descartarse por presión de memoria; si se llena, la escritura falla de forma **visible** |
| `save ""` / `appendonly no` | sin persistencia | el caché es **efímero**: se repuebla con el seed en cada arranque del contenedor |
| `protected-mode no` / `bind 0.0.0.0` | abierto en la red de compose | entorno local de experimento, sin credenciales |

## Esquema de claves (lo escribe/lee `ms-perfil-riesgo`)

| Key | Value | TTL | Escritura / lectura |
|---|---|---|---|
| `profile:{customer_id}` | string JSON (modelo de abajo) | `CACHE_TTL_S` (86400 s) en cada `SET` | `SET` tras un cálculo en vivo correcto (refresca el respaldo); `GET` durante el enmascaramiento ASR2 |
| `processed:{correlation_id}` | string JSON con el `ProfileEvaluationResult` publicado | `PROCESSED_TTL_S` (3600 s) | `SET` **después** de publicar el resultado con éxito; `GET` al entrar la tarea: si existe, se **re-publica ese mismo resultado** y se hace `ack` sin recalcular |

> El valor de `processed:{correlation_id}` **no** es un centinela `"1"`: guarda el
> resultado completo justamente para poder reemitirlo idéntico ante una
> reentrega.

### Modelo JSON de `profile:{customer_id}`

| Atributo | Tipo | Propósito |
|---|---|---|
| `customer_id` | string | dueño del perfil |
| `score` | number | score de riesgo 0–100 |
| `category` | string | `LOW` \| `MEDIUM` \| `HIGH` |
| `calculated_at` | string (ISO-8601 UTC) | antigüedad del respaldo (se usa para `cache.age_s` en el span) |
| `model_version` | string | versión del algoritmo; si `!=` `MODEL_VERSION` actual → span con `solventa.cache.stale_version=true`, pero el respaldo **se usa igual** |
| `snapshot_type` | string | siempre `LIVE_EVALUATION` (un respaldo nace de un cálculo exitoso) |
| `correlation_id` | string | evaluación que lo generó |
| `sources` | object | `{ "open_data": "ok", "open_finance": "ok" }` — solo para análisis, no se propaga al resultado |

## Seed (`seed/profiles.redis`)

Comandos `SET ... EX 86400` para los clientes de prueba **`C001`–`C005`**.
**`C006` se omite a propósito**: es el caso de *cache miss* de ASR2
(`DEGRADED_NO_FALLBACK`).

| Cliente | category / score | model_version / antigüedad | Rol en el experimento |
|---|---|---|---|
| `C001` | `LOW` / 15 | `v1`, fresco | línea base |
| `C002` | `MEDIUM` / 55 | `v1`, fresco | respaldo disponible si el retry no alcanza |
| `C003` | `HIGH` / 88 | `v1`, fresco | ASR2 con respaldo fresco |
| `C004` | `MEDIUM` / 60 | `v1`, `calculated_at` ~20 h atrás | ASR2 con respaldo viejo pero válido |
| `C005` | `HIGH` / 91 | **`v0`** (versión obsoleta) | ASR2 con `stale_version=true` |
| `C006` | — (sin clave) | — | ASR2 sin respaldo → `DEGRADED_NO_FALLBACK` |

La carga la hace la propia imagen: `entrypoint.sh` lanza `redis-server`, espera
al `PONG` y ejecuta `redis-cli < profiles.redis`. Ocurre en **cada** arranque del
contenedor (`docker compose up`, con o sin perfil `experimento`), es idempotente
y no necesita servicios ni jobs aparte. `REDIS_SEED_FILE` permite apuntar a otro
archivo.

> Para reiniciar el estado del caché entre corridas: `docker compose down -v` (o
> `docker compose --profile experimento down -v`) y volver a levantar.

El umbral `< 100 ms` de ASR2 se mide en `ms-perfil-riesgo` (span
`profile.cache_lookup` alrededor del `GET`), no dentro de Redis.

## Inspección

```sh
docker compose exec redis redis-cli KEYS 'profile:*'
docker compose exec redis redis-cli GET  profile:C004
docker compose exec redis redis-cli KEYS 'processed:*'
```
