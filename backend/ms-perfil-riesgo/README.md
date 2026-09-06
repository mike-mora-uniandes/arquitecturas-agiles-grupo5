# ms-perfil-riesgo

Corazón del experimento. Consume la solicitud de evaluación de RabbitMQ, calcula
el perfil de riesgo consultando Open Data / Open Finance y **aplica las tres
tácticas de disponibilidad** (ASR1 detección, ASR3 reintento, ASR2
enmascaramiento con caché). Publica el `ProfileEvaluationResult` hacia
`ms-notificaciones`.

API Flask + worker Celery **en el mismo contenedor** (`run.sh`, ambos bajo
`opentelemetry-instrument`, unidos con `wait -n`: si uno cae, el contenedor cae y
se ve en `docker compose ps`). Único microservicio con Redis y con salida HTTP a
las fuentes externas. Sin persistencia local: `GET /profiles/<customer_id>`
responde `501`.

> El contrato (mensajes, topología RabbitMQ, esquema de Wiremock, nombres OTel)
> está definido en `../DESIGN.md` §2 e implementado aquí. Si se cambia, se
> ajustan `config.py` (colas/exchange/tarea de resultado) y `mensajes.py`.

## Flujo del worker (`tareas/evaluacion.py`, tarea `perfil.evaluate_profile`)

1. **Parseo** del contrato (`mensajes.parse_request`). Payload ilegible o sin
   `correlation_id` / `customer_id` → `Reject(requeue=false)` → DLQ.
2. **Idempotencia**: `GET processed:{correlation_id}`. Si existe → re-publica ese
   mismo resultado y termina (`"republished"`), sin recalcular.
3. **ConsultaPerfil** (`logica/consulta_perfil.py`): llama a Open Data y Open
   Finance **en paralelo** (`ThreadPoolExecutor`, contexto OTel propagado a los
   hilos). Timeout por intento = `DETECTION_TIMEOUT_MS`. Presupuesto común de
   reintentos = `RETRY_BUDGET_MS` desde el inicio.
4. **Detección — ASR1** (`logica/deteccion_excepciones.py`): clasifica el fallo
   de cada fuente (`timeout` / `connection` / `http_5xx` / `anomalous`) y
   registra la **primera** detección → span `profile.detection`,
   `solventa_profile_detection_ms`.
5. **Retry — ASR3**: para fallos reintentables (`timeout`, `connection`,
   `http_5xx`/`429`), `tenacity` con backoff exponencial + *full jitter*
   (`RETRY_BACKOFF_BASE_MS`), `≤ RETRY_MAX` intentos, cortado por el presupuesto
   → span `profile.retry`. `anomalous` y `4xx` (salvo `429`) **no** se reintentan.
6. **Rama**:
   - **ambas fuentes con dato válido** → `CalculoPerfil`
     (`score = round(0.6·financial_risk + 0.4·data_risk)`;
     `LOW < 34 ≤ MEDIUM ≤ 66 < HIGH`) → `SET profile:{customer_id}` (refresca el
     respaldo). `source = LIVE` (sin reintentos) o `RETRY` (≥1 reintento).
   - **alguna sin dato válido** → **enmascaramiento ASR2**
     (`logica/manejo_excepciones.py` → `logica/cache_externos.py`):
     `GET profile:{customer_id}`. Hit → `status=DEGRADED`, `source=CACHE`.
     Miss → `status=DEGRADED_NO_FALLBACK`, `profile=null`, `reason`.
     Span `profile.cache_lookup`, `solventa_profile_cache_ms`.
7. **Publicación**: `send_task` del `ProfileEvaluationResult` al exchange
   `solventa` / rk `profile.result` (nombre `notificaciones.deliver_result`).
   Tras publicar → `SET processed:{correlation_id}` con el resultado + `ack`.

`OK`, `DEGRADED` y `DEGRADED_NO_FALLBACK` son todos «éxito» para la cola (se hace
`ack`). Solo una excepción no controlada del worker manda el mensaje a la DLQ.

## Módulos

| Ruta | Rol | ASR |
|---|---|---|
| `logica/fuentes_externas.py` | cliente HTTP `requests` + validación de esquema de la respuesta | — |
| `logica/deteccion_excepciones.py` | vocabulario de fallos + excepciones `FalloReintentable` / `RespuestaAnomala` | ASR1 |
| `logica/consulta_perfil.py` | concurrencia + `tenacity` + presupuesto de tiempo | ASR1 / ASR3 |
| `logica/calculo_perfil.py` | `score` / `category` (determinista) | — |
| `logica/manejo_excepciones.py` | arma el resultado degradado desde el caché | ASR2 |
| `logica/cache_externos.py` | `GET`/`SET` de `profile:{customer_id}` + `age_s` / `stale_version` | ASR2 |
| `tareas/evaluacion.py` | orquesta el flujo de arriba; `celery_app` en `extensiones.py` | — |
| `tareas/publicador.py` | publica el `ProfileEvaluationResult` | — |
| `mensajes.py` | parseo/armado del contrato + enums (`OK`/`DEGRADED`/…`LIVE`/`RETRY`/`CACHE`) | — |
| `telemetria.py` | tracer + histogramas/contadores `solventa_profile_*`; reinicia el `MeterProvider` por proceso hijo del pool prefork | — |
| `topologia.py` | declara `solventa.dlx` y `profile.{request,result}.dead.q` al `worker_ready` | — |
| `vistas/perfiles_riesgo.py` | `GET /profiles/<customer_id>` → `501` (fuera de alcance) | — |

## Observabilidad (`../DESIGN.md` §2.4)

Spans: `profile.evaluation` (raíz), `profile.detection`, `profile.retry`,
`profile.cache_lookup`, `profile.calculation`, `profile.publish`.

Métricas (histogramas `*_ms` + contadores):
`solventa_profile_detection_ms`, `solventa_profile_retry_ms` / `_attempts`,
`solventa_profile_cache_ms`, `solventa_profile_cache_hit_total`,
`solventa_profile_evaluation_ms` / `_total{status,source}`, y las señales
directas de cumplimiento `solventa_profile_asr{1,2,3}_within_*_total{pass}`.

Sin telemetría por defecto (`OTEL_SDK_DISABLED=true`); el perfil `experimento` lo
activa.

## Variables de entorno (ver `../.env.example`)

| Variable | Def. | Uso |
|---|---|---|
| `RABBITMQ_URL` | `amqp://guest:guest@rabbitmq:5672//` | broker |
| `REDIS_URL` | `redis://redis:6379/0` | caché + idempotencia |
| `OPEN_DATA_URL` / `OPEN_FINANCE_URL` | `http://wiremock:8080/open-{data,finance}` | fuentes externas |
| `DETECTION_TIMEOUT_MS` | `700` | ASR1: timeout por intento |
| `RETRY_MAX` | `3` | ASR3: intentos máximos |
| `RETRY_BACKOFF_BASE_MS` | `200` | ASR3: base del backoff |
| `RETRY_BUDGET_MS` | `5000` | ASR3: presupuesto total |
| `CACHE_TTL_S` | `86400` | ASR2: TTL de `profile:{id}` |
| `CACHE_ASR2_THRESHOLD_MS` | `100` | ASR2: umbral de la señal de cumplimiento |
| `PROCESSED_TTL_S` | `3600` | TTL de `processed:{correlation_id}` |
| `CELERY_CONCURRENCY` | `4` | procesos del pool prefork |
| `RABBITMQ_EXCHANGE` / `RABBITMQ_DLX` / `REQUEST_QUEUE` / `RESULT_QUEUE` / `*_ROUTING_KEY` / `RESULT_TASK_NAME` | ver `config.py` | topología |
| `SCHEMA_VERSION` / `MODEL_VERSION` | `1` / `v1` | contrato / cálculo |

## Pruebas

14 pruebas unitarias (`pytest` + `responses` + `fakeredis`; sin broker ni Redis
reales — `conftest.py` usa `task_always_eager`, broker `memory://` y
`fakeredis`).

```sh
cd ms-perfil-riesgo
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest tests
python -m pytest tests/test_flujo_evaluacion.py::test_idempotencia_republica_sin_recalcular
```

| Archivo | Cubre |
|---|---|
| `tests/test_fuentes_externas.py` | cliente HTTP + validación de esquema (5) |
| `tests/test_calculo_perfil.py` | fórmula de `score` / `category` (2) |
| `tests/test_cache_externos.py` | lectura/escritura del respaldo (2) |
| `tests/test_flujo_evaluacion.py` | flujo completo: LIVE / RETRY / DEGRADED / DEGRADED_NO_FALLBACK / idempotencia (5) |

Dentro del contenedor:

```sh
docker compose exec ms-perfil-riesgo sh -c \
  "pip install -q -r requirements-dev.txt && python -m pytest -q tests"
```

## Dependencias

Sobre `solventa/flask-base`: `redis==5.2.1`, `tenacity==9.0.0`
(+ `pytest` / `responses` / `fakeredis` en `requirements-dev.txt`, no van en la
imagen).
