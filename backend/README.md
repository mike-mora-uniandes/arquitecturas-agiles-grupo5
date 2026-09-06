# Backend Solventa — Microservicios

Backend del **experimento de disponibilidad** de Solventa. Un analista de riesgo
solicita la evaluación del perfil de un cliente; el flujo aplica tres tácticas
ante fallos de las fuentes externas Open Data / Open Finance:

| ASR | Táctica | Criterio de «hecho» |
|---|---|---|
| **ASR1** | Exception Detection | detectar el fallo de una fuente en `< 700 ms` |
| **ASR3** | Retry | backoff exponencial + jitter, `≤ 3` intentos, `≤ 5 s` totales |
| **ASR2** | Exception Handling | degradar leyendo el respaldo de Redis en `< 100 ms` adicionales, sin error visible al analista |

Las tres viven en `ms-perfil-riesgo`. `../DESIGN.md` (local, no versionado) tiene
el detalle del flujo (§1.4) y los contratos (§2).

## Estado

| Componente | Estado |
|---|---|
| Estructura + `docker-compose` + imagen base Flask/Python | ✅ |
| Imagen Redis (respaldo ASR2 + idempotencia) | ✅ |
| **`ms-perfil-riesgo` — ASR1 / ASR2 / ASR3** | ✅ implementado y verificado E2E, 14 pruebas unitarias |
| **`ms-riesgos` — `POST /evaluations` → publica al broker** | ✅ implementado, 3 pruebas |
| **`ms-notificaciones` — consumer del resultado** | ✅ consume `profile.result.q` y registra el resultado (Celery); notificación real fuera de alcance del experimento |
| Wiremock (escenarios por `customer_id`) | ✅ |
| Observabilidad (OTel Collector + Prometheus + Grafana) | ✅ pipeline + dashboard con panel por ASR |
| Carga (Locust) | ✅ `locustfile.py` con matriz `E0`–`E5` |

## Estructura

```
backend/
├── README.md                 # este archivo (guía operativa)
├── DESIGN.md                 # decisiones + contratos (local, gitignored)
├── docker-compose.yml        # 6 servicios core + 3 del perfil 'experimento' (+ locust siempre)
├── build-base.sh / .ps1      # construye la imagen base y levanta el stack
├── .env.example              # plantilla de configuración (se copia a .env)
│
├── base-image/               # solventa/flask-base — Flask + Celery + requests + OpenTelemetry
│   ├── Dockerfile            # python:3.12-slim fijado por digest
│   └── requirements-base.txt # versiones alineadas con MISW4201-202614-Backend-Grupo08
│
├── ms-riesgos/               # API HTTP de entrada; publica perfil.evaluate_profile
│   ├── app.py  config.py  extensiones.py  run.sh  Dockerfile
│   ├── tareas/publicacion.py
│   └── tests/test_app.py
│
├── ms-perfil-riesgo/         # cálculo del perfil + ASR1/ASR2/ASR3   ← núcleo del experimento
│   ├── app.py  config.py  extensiones.py  mensajes.py  telemetria.py  topologia.py  run.sh  Dockerfile
│   ├── logica/               # fuentes_externas, deteccion_excepciones, consulta_perfil,
│   │                         #   calculo_perfil, manejo_excepciones, cache_externos
│   ├── tareas/               # evaluacion.py (tarea Celery), publicador.py
│   ├── vistas/perfiles_riesgo.py   # GET /profiles/<id> → 501
│   └── tests/                # 14 pruebas (pytest + responses + fakeredis)
│
├── ms-notificaciones/        # consume profile.result.q y loguea el resultado
│   ├── app.py  config.py  extensiones.py  telemetria.py  run.sh  Dockerfile
│   └── tareas/entrega.py
│
├── redis/                    # solventa/redis — redis.conf efímero + entrypoint que carga el seed
│   └── seed/profiles.redis   # C001–C005 (C006 ausente a propósito)
│
├── wiremock/mappings/        # open-data.json / open-finance.json — escenario por customer_id
│
├── observabilidad/
│   ├── otel-collector.yaml   prometheus.yml
│   └── grafana/provisioning/ # datasource + dashboard solventa-experimento.json
│
└── experimento/
    ├── locustfile.py                # VU del analista; matriz E0–E5 por customer_id
    ├── run_asr_tests.ps1            # helper: pesos por ASR para una corrida
    └── test_locust_scenarios.py    # pytest de la matriz
```

Cada microservicio espeja el layout **plano** de `ms-perfil-riesgo/` (`app.py`,
`config.py`, `extensiones.py`, `run.sh`, `Dockerfile`, `vistas/ logica/ tareas/
tests/`). `config.py` es una clase `Config` leída íntegramente de variables de
entorno; `run.sh` lanza el worker Celery + `gunicorn --workers 1` bajo
`opentelemetry-instrument`, unidos con `wait -n`.

Cada subcarpeta (`ms-*/`, `redis/`, `wiremock/`, `rabbitmq/`, `observabilidad/`,
`observabilidad/grafana/provisioning/dashboards/`, `experimento/`) tiene su
`README.md` con el detalle de ese componente.

## Servicios y puertos

| Servicio | Host:contenedor | Perfil | Descripción |
|---|---|---|---|
| `ms-riesgos` | `5001:5000` | core | `POST /evaluations` (alias `/riesgos/evaluar`) → publica `perfil.evaluate_profile` |
| `ms-perfil-riesgo` | `5002:5000` | core | worker de evaluación + ASR1/ASR2/ASR3; `GET /profiles/<id>` → 501 |
| `ms-notificaciones` | `5003:5000` | core | consume `profile.result.q`, loguea el `ProfileEvaluationResult` |
| `rabbitmq` | `5672`, `15672` | core | broker AMQP (consola `guest`/`guest`) |
| `redis` | `6379` | core | respaldo ASR2 + idempotencia; `noeviction`, efímero, seed al arrancar |
| `wiremock` | `8080` | core | Open Data / Open Finance simulados |
| `otel-collector` | `4318`, `9464` | **experimento** | recibe OTLP, expone métricas a Prometheus |
| `prometheus` | `9090` | **experimento** | scrape del collector cada 5 s |
| `grafana` | `3000` | **experimento** | dashboard del experimento (anónimo/Admin) |
| `locust` | `8089` | core | generador de carga; apunta a `http://ms-riesgos:5000` |

No hay `healthcheck` en ningún servicio ni endpoint `/health`: la vida del worker
la garantiza el `wait -n` de `run.sh`; se verifica con `docker compose ps` + logs.

## Flujo de un mensaje

```
analista / Locust
  │  POST /evaluations {customer_id}
  ▼
ms-riesgos ── send_task("perfil.evaluate_profile") ──▶ exchange "solventa"  (rk profile.request)
                                                          │
                                                          ▼  profile.request.q
                                              ms-perfil-riesgo  (worker Celery)
                                                 1. idempotencia (processed:{cid})
                                                 2. Open Data + Open Finance en paralelo
                                                 3. ASR1 detección  ·  4. ASR3 retry
                                                 5. ambas OK → cálculo + SET profile:{id}
                                                    alguna falla → ASR2  GET profile:{id}
                                                 6. send_task("notificaciones.deliver_result")
                                                          │  (rk profile.result)
                                                          ▼  profile.result.q
                                                   ms-notificaciones → log
```

Celery/Kombu **es** el bus: los productores usan `send_task(nombre, [payload],
exchange=, routing_key=)`; cada servicio declara su cola (kombu `Queue` con args
`x-dead-letter-*`) en su `extensiones.py`. Colas **clásicas durables** (no quorum:
Celery 5.4 aplica QoS global). El DLX `solventa.dlx` y las colas
`profile.{request,result}.dead.q` los declara `ms-perfil-riesgo/topologia.py` al
arrancar. Contratos de mensaje: `../DESIGN.md` §2.1.

## Requisitos

- Docker Desktop con Compose v2 (`docker compose version`).
- Puertos libres: 5001–5003, 5672, 6379, 8080, 8089, 15672 (+ 3000, 4318, 9090,
  9464 en modo experimento).

## Puesta en marcha

Todo se ejecuta desde `backend/`.

### 1. Modo normal (flujo funcional, sin métricas)

```powershell
./build-base.ps1        # Windows PowerShell
```
```sh
sh build-base.sh        # Git Bash / Linux / macOS   (--no-up = solo construir la imagen base)
```

El script: (1) crea `.env` desde `.env.example` si no existe; (2) construye
`solventa/flask-base` — **paso previo obligatorio, no es un servicio de
compose**; (3) `docker compose up -d --build`; (4) `docker compose ps`.

> Si cambias algo en `base-image/`, vuelve a ejecutar el script: un
> `docker compose up` a secas **no** reconstruye la imagen base.

Prueba rápida:

```sh
curl -s -XPOST http://localhost:5001/evaluations \
  -H 'Content-Type: application/json' \
  -d '{"customer_id":"C001","requested_by":"analista-07"}'
docker compose logs ms-notificaciones | grep "ProfileEvaluationResult recibido"
```

### 2. Ejecutar el experimento de arquitectura (con métricas y carga)

1. **Activar la telemetría** en `.env`:

   ```
   OTEL_SDK_DISABLED=false
   OTEL_TRACES_EXPORTER=otlp
   OTEL_METRICS_EXPORTER=otlp
   ```

   (opcional) `OTEL_METRIC_EXPORT_INTERVAL=5000` para ver los ASR casi en vivo.

2. **Construir la imagen base** (`solventa/flask-base`, paso previo obligatorio):

   ```sh
   sh build-base.sh --no-up          # Git Bash / Linux / macOS
   ```

   o, sin el script (PowerShell puro, o si prefieres el comando crudo — es lo
   mismo que hace `build-base.sh`):

   ```sh
   docker build -t solventa/flask-base:latest ./base-image
   ```

3. **Levantar el stack completo** (observabilidad + Locust incluidos, no solo el
   stack base):

   ```sh
   docker compose --profile experimento up -d --build
   docker compose ps
   ```

   Añade `otel-collector`, `prometheus` y `grafana` a los 6 servicios core y a
   `locust`.

4. **Esperar a que el worker esté listo**:

   ```sh
   docker compose ps
   docker compose logs ms-perfil-riesgo | grep "celery@.* ready"
   ```

5. **Lanzar la carga con Locust** — abrir http://localhost:8089

   Aparece la pantalla **«Start new load test»**. Rellenar:

   | Campo del formulario | Qué poner |
   |---|---|
   | **Number of users (peak concurrency)** | usuarios concurrentes de la fase (columna *Usuarios* de la tabla de abajo) |
   | **Ramp up (users started/second)** | ritmo de arranque (columna *Spawn*) |
   | **Host** | ya viene relleno con `http://ms-riesgos:5000` (es el `--host` del contenedor). Si ejecutas Locust en local, cámbialo a `http://localhost:5001` |
   | **Advanced options → Run time** | duración de la fase, p. ej. `2m`, `5m`, `10m` (columna *Duración*). Si se deja vacío, corre hasta pulsar *Stop* |

   Pulsar **START**. La barra superior pasa de `STATUS: READY` a `RUNNING` y
   muestra `RPS` y `FAILURES` en vivo. **`FAILURES` debe quedarse en `0%`**:
   cuenta respuestas HTTP no-2xx de `ms-riesgos`; un resultado `DEGRADED` **no**
   es un fallo aquí (la API responde `202` igual), la degradación se ve en
   Grafana. Al terminar el *Run time* (o con *Stop*) se pueden descargar los
   *Download Data* (CSV) y el *Report* (HTML) desde la pestaña correspondiente.

   Fases sugeridas (`../DESIGN.md` §2.5) — una corrida por fila:

   | Fase | Usuarios | Spawn | Duración (Run time) | Mezcla |
   |---|---|---|---|---|
   | Baseline | 5 | 1 | 2m | solo `C001` |
   | Carga con fallos | 20–30 | 2 | 5m–10m | `E0`–`E5` (40 % `C001`, resto repartido) |
   | Pico (opcional) | 50 | 5 | 3m | misma mezcla |

   > La captura de referencia del equipo usa `10` / `5` / `5m` como valores de
   > ejemplo para una prueba rápida.

   **Pesos de la mezcla**: por defecto (`E0=40 E1=18 E2=15 E3=15 E4=8 E5=4`)
   están en `locustfile.py`. Para enfatizar un ASR concreto: ejecuta Locust en
   local con `experimento/run_asr_tests.ps1 ASR1|ASR2|ASR3|BASE` (fija los
   `E*_WEIGHT`), **o** añade esos `E*_WEIGHT` a un bloque `environment:` del
   servicio `locust` en `docker-compose.yml` y recrea el contenedor (el servicio
   `locust` no lee `.env`).

   Cada escenario y su resultado esperado:

   | `customer_id` | Escenario Wiremock | ASR ejercitadas | `status` / `source` |
   |---|---|---|---|
   | `C001` (`E0`) | OK | línea base | `OK` / `LIVE` |
   | `C002` (`E1`) | latencia lognormal (a veces > 700 ms) | ASR1 + ASR3 | `OK` / `RETRY` o `DEGRADED` / `CACHE` |
   | `C003` (`E2`) | `503` en ambas fuentes | ASR1 + ASR3 → ASR2 | `DEGRADED` / `CACHE` |
   | `C004` (`E3`) | `503` en ambas fuentes | ASR2 (respaldo viejo válido) | `DEGRADED` / `CACHE` |
   | `C005` (`E4`) | payload anómalo en ambas | ASR1 → ASR2 | `DEGRADED` / `CACHE` (`stale_version=true`) |
   | `C006` (`E5`) | `503`, sin respaldo en Redis | ASR2 sin caché | `DEGRADED_NO_FALLBACK` / `CACHE` |

6. **Observar en Grafana** — http://localhost:3000 → dashboard
   *«Solventa - Experimento de disponibilidad (PerfilRiesgo)»*:
   - *Resumen*: tasa de éxito global (≈100 %), `DEGRADED_NO_FALLBACK` solo por
     `C006`.
   - *ASR1 / ASR2 / ASR3*: P99 vs. la línea de umbral (700 / 100 / 5000 ms) y el
     `% que cumple` (contadores `solventa_profile_asr{1,2,3}_within_*_total`).
   - *Latencia end-to-end*: P50 / P99 de `solventa_profile_evaluation_ms`.

7. **Reiniciar entre corridas** (repuebla Redis, limpia colas y métricas):

   ```sh
   docker compose --profile experimento down -v
   ```

### Detener

```sh
docker compose down                              # modo normal
docker compose --profile experimento down -v     # experimento (y borra volúmenes)
```

## Pruebas unitarias

| Servicio | Pruebas | Comando (desde la carpeta del servicio) |
|---|---|---|
| `ms-perfil-riesgo` | 14 (`pytest` + `responses` + `fakeredis`) | `pip install -r requirements.txt -r requirements-dev.txt && python -m pytest tests` |
| `ms-riesgos` | 3 (`pytest`, `send_task` mockeado) | `pip install -r requirements.txt && python -m pytest tests` |
| `experimento` | 2 (matriz del `locustfile`) | `python -m pytest test_locust_scenarios.py` |

Dentro del contenedor:

```sh
docker compose exec ms-perfil-riesgo sh -c \
  "pip install -q -r requirements-dev.txt && python -m pytest -q tests"
```

## Configuración (`.env`)

`docker-compose.yml` carga `.env` vía `env_file` en los tres microservicios (no
en `locust` ni en la infraestructura). Claves principales:

| Bloque | Variables |
|---|---|
| Broker / caché / fuentes | `RABBITMQ_URL`, `REDIS_URL`, `OPEN_DATA_URL`, `OPEN_FINANCE_URL` |
| Tácticas (ASR) | `DETECTION_TIMEOUT_MS`, `RETRY_MAX`, `RETRY_BACKOFF_BASE_MS`, `RETRY_BUDGET_MS`, `CACHE_TTL_S`, `CACHE_ASR2_THRESHOLD_MS` |
| Idempotencia / worker | `PROCESSED_TTL_S`, `CELERY_CONCURRENCY` |
| Observabilidad | `OTEL_SDK_DISABLED`, `OTEL_TRACES_EXPORTER`, `OTEL_METRICS_EXPORTER`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_METRIC_EXPORT_INTERVAL` |
| Común | `LOG_LEVEL`, `FLASK_ENV` |

## Flujo de trabajo

- Ramas `feature/*` desde `develop`; PR hacia `develop`; `main` para versiones
  estables.
- Conventional Commits en español (`fix:`, `feat(wiremock): …`).
- `.gitattributes` fuerza LF: en Windows, cuidado con editores que reescriban
  `.sh` como CRLF (se rompen dentro de los contenedores Linux).
