# redis

Imagen Redis de Solventa: **caché de datos externos** de MS PerfilRiesgo, usada
para la táctica *Exception Handling* (ASR2), y almacén de la marca de
idempotencia.

## Configuración (`redis.conf`)

- `maxmemory 128mb`, `maxmemory-policy noeviction` — el caché es un valor de
  respaldo; no debe descartarse por presión de memoria.
- `save ""`, `appendonly no` — **efímero**. Se repuebla con el seed en cada
  arranque del contenedor (ver *Seed*).

## Esquema de claves (lo implementa MS PerfilRiesgo)

| Key | Value | TTL |
|---|---|---|
| `profile:{customer_id}` | string JSON (modelo de abajo) | `CACHE_TTL_S` en cada `SET` |
| `processed:{correlation_id}` | `"1"` | `PROCESSED_TTL_S` (idempotencia, `SET NX EX`) |

### Modelo JSON de `profile:{customer_id}`

| Attribute | Type | Purpose |
|---|---|---|
| `customer_id` | string | dueño del perfil |
| `score` | number | score de riesgo 0–100 |
| `category` | string | `LOW` \| `MEDIUM` \| `HIGH` |
| `calculated_at` | string (ISO-8601 UTC) | antigüedad del respaldo |
| `model_version` | string | versión del algoritmo |
| `snapshot_type` | string | siempre `LIVE_EVALUATION` (un respaldo nace de un cálculo exitoso) |
| `correlation_id` | string | evaluación que lo generó |
| `sources` | object | `{ "open_data": "ok", "open_finance": "ok" }` — solo para análisis |

## Seed

`seed/profiles.redis` — comandos `SET ... EX` de los clientes de prueba
`C001`–`C005`. **`C006` no está a propósito**: prueba el *cache miss* de ASR2.

Lo carga la propia imagen: `entrypoint.sh` arranca `redis-server` y, en cuanto
responde, ejecuta `redis-cli < profiles.redis`. Ocurre en cada arranque del
contenedor (`docker compose up`, con o sin perfil `experimento`); es idempotente
y no requiere servicios ni jobs externos. Se puede apuntar a otro archivo con la
variable `REDIS_SEED_FILE`.

El `< 100 ms` de ASR2 se mide en MS PerfilRiesgo (span alrededor del `GET`), no
en Redis.
