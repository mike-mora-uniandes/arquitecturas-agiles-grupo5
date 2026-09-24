# arquitecturas-agiles-grupo5

Repositorio de trabajo del **Grupo 5** para la asignatura **Arquitecturas
Ágiles** (MISO), sobre el proyecto **Solventa**.

Contiene **dos experimentos independientes**, cada uno en su propio
directorio de nivel superior con su propio `docker-compose.yml`, imagen base
y rango de puertos (`backend/` usa `5001+`, `seguridad/` usa `6001+`), para
poder levantar ambos stacks a la vez sin choques:

| Experimento | Directorio | Atributo de calidad | Estado |
|---|---|---|---|
| **1 — Disponibilidad** | [`backend/`](backend/README.md) | *Availability* — tolerar fallos de Open Data / Open Finance | ✅ implementado y verificado (ASR1/ASR2/ASR3) |
| **2 — Seguridad** | [`seguridad/`](seguridad/README.md) | *Confidentiality* + *Integrity* — detectar y reaccionar ante extracción/alteración no autorizada del perfil | ✅ implementado y verificado (ASR1–ASR4) |

## Estructura del repositorio

```
.
├── README.md                 # este archivo
├── LICENSE
│
├── backend/                  # Experimento 1 — disponibilidad (puertos 5001+)
│   ├── README.md             # ▶ guía operativa detallada (estructura, ejecución, pruebas)
│   ├── DESIGN.md             # decisiones + contratos (local, gitignored)
│   ├── docker-compose.yml
│   ├── build-base.sh / .ps1
│   ├── .env.example
│   ├── base-image/           # solventa/flask-base (Flask + Celery + requests + OpenTelemetry)
│   ├── ms-riesgos/           # API de entrada                → backend/ms-riesgos/README.md
│   ├── ms-perfil-riesgo/     # cálculo + ASR1/ASR2/ASR3      → backend/ms-perfil-riesgo/README.md
│   ├── ms-notificaciones/    # consumer del resultado        → backend/ms-notificaciones/README.md
│   ├── redis/                # imagen Redis + seed           → backend/redis/README.md
│   ├── wiremock/             # Open Data / Open Finance       → backend/wiremock/README.md
│   ├── rabbitmq/             # notas del broker              → backend/rabbitmq/README.md
│   ├── observabilidad/       # OTel Collector + Prometheus + Grafana → backend/observabilidad/README.md
│   └── experimento/          # carga con Locust (matriz E0–E5)  → backend/experimento/README.md
│
└── seguridad/                 # Experimento 2 — confidencialidad + integridad (puertos 6001+)
    ├── README.md             # ▶ guía operativa detallada (estructura, ejecución, ataques)
    ├── docker-compose.yml
    ├── build-base.sh
    ├── .env.example
    ├── base-image/           # solventa/security-flask-base
    ├── seed/                 # Faker — puebla las 3 bases    → seguridad/seed/README.md
    ├── experimento/          # ataques (JWT forjado, mitmproxy, Locust) → seguridad/experimento/README.md
    ├── ms-identidad/         # auth/roles + BOLA deliberado  → seguridad/ms-identidad/README.md
    ├── ms-cliente/           # entrada + verificación integridad → seguridad/ms-cliente/README.md
    ├── ms-riesgo/            # perfil + firma de integridad  → seguridad/ms-riesgo/README.md
    ├── ms-audit/             # clasifica intrusiones         → seguridad/ms-audit/README.md
    ├── ms-notificaciones/    # notifica al analista          → seguridad/ms-notificaciones/README.md
    └── observabilidad/       # OTel Collector + Prometheus + Grafana → seguridad/observabilidad/README.md
```

Cada subcarpeta de `backend/` y `seguridad/` tiene su propio `README.md` con
el detalle del componente. Ambos experimentos comparten el mismo layout
plano por microservicio (`app.py`, `config.py`, `extensiones.py`, `run.sh`,
`Dockerfile`, `vistas/ logica/ tareas/ tests/`) y el mismo *language split*:
español para identificadores/comentarios/commits internos, inglés para todo
lo que viaja "en el cable" (JSON, colas, routing keys, env vars, nombres
OTel).

## Experimento 1 — Disponibilidad

Un analista de riesgo solicita la evaluación del perfil de un cliente y el
flujo aplica tres tácticas ante fallos de las fuentes externas Open Data /
Open Finance.

| ASR | Táctica | Objetivo |
|---|---|---|
| **ASR1** | *Exception Detection* | detectar el fallo de una fuente en `< 700 ms` |
| **ASR3** | *Retry* | backoff exponencial + jitter, `≤ 3` intentos, `≤ 5 s` totales |
| **ASR2** | *Exception Handling* | degradar con el respaldo de Redis en `< 100 ms` extra, sin error visible al analista |

### Arquitectura

Tres microservicios Python (Flask + Celery) sobre un **Event Bus** RabbitMQ:

```
analista/Locust ─POST /evaluations─▶ ms-riesgos ─(profile.request)─▶ ms-perfil-riesgo ─(profile.result)─▶ ms-notificaciones
                                                        │  ASR1 / ASR3 / ASR2
                                          Open Data / Open Finance (Wiremock) · respaldo en Redis
```

- **`ms-riesgos`** — API HTTP de entrada; genera el `correlation_id` y publica la
  solicitud de forma asíncrona. No espera respuesta.
- **`ms-perfil-riesgo`** — consume la solicitud, consulta las fuentes externas en
  paralelo y **aplica las tres tácticas**; calcula el perfil o lo degrada desde
  la caché. Único servicio con Redis y salida HTTP.
- **`ms-notificaciones`** — consume el resultado y lo registra en el log
  (evidencia end-to-end del Event Bus; la notificación real al analista está
  fuera del alcance del experimento).
- **Infra**: RabbitMQ (broker), Redis (respaldo ASR2 + idempotencia), Wiremock
  (fuentes externas simuladas por `customer_id`), y — en el perfil
  `experimento` — OpenTelemetry Collector + Prometheus + Grafana, con Locust como
  generador de carga.

El diseño detallado y los contratos vigentes (mensajes, topología RabbitMQ,
esquema de Wiremock, nombres OTel) están en `backend/DESIGN.md` (documento local,
no versionado).

### Estado

| Componente | Estado |
|---|---|
| Estructura + `docker-compose` + imagen base Flask/Python | ✅ |
| Imagen Redis (respaldo ASR2 + idempotencia) | ✅ |
| **`ms-perfil-riesgo` — ASR1 / ASR2 / ASR3** | ✅ implementado y verificado E2E (14 pruebas) |
| **`ms-riesgos` — `POST /evaluations` → publica al broker** | ✅ implementado (3 pruebas) |
| **`ms-notificaciones` — consumer del resultado** | ✅ consume `profile.result.q` y registra el resultado (log = evidencia E2E; notificación real fuera de alcance) |
| Wiremock (escenarios por `customer_id`) | ✅ |
| Observabilidad (OTel Collector + Prometheus + Grafana) | ✅ pipeline + dashboard con panel por ASR |
| Carga (Locust) | ✅ matriz `E0`–`E5` |

### Puesta en marcha rápida

> [!NOTE]
> Levanta el stack base (6 microservicios + infra) en modo normal para probar el
> flujo funcional de extremo a extremo, sin métricas ni generador de carga.

Requisitos: Docker Desktop con Compose v2. Todo se ejecuta desde `backend/`.

```powershell
cd backend
./build-base.ps1        # Windows PowerShell
```
```sh
cd backend
sh build-base.sh        # Git Bash / Linux / macOS
```

El script crea `.env` desde `.env.example`, construye la imagen base
`solventa/flask-base` (paso previo, **no** es un servicio de compose) y levanta
el stack.

```sh
# probar el flujo
curl -s -XPOST http://localhost:5001/evaluations \
  -H 'Content-Type: application/json' -d '{"customer_id":"C001"}'

# experimento completo (métricas + carga): ver backend/README.md § "Ejecutar el experimento"
docker compose --profile experimento up -d --build
```

**Los pasos precisos del experimento (activar telemetría, fases de carga en
Locust, lectura del dashboard de Grafana, reinicio entre corridas) están en
[`backend/README.md`](backend/README.md).**

### Ejecutar el experimento de disponibilidad (con métricas y carga)

> [!NOTE]
> Levanta el stack completo (observabilidad + Locust), genera carga con fallos
> simulados por escenario y mide en Grafana el cumplimiento de ASR1 / ASR2 / ASR3.

Todo se ejecuta desde `backend/`.

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

## Experimento 2 — Seguridad (confidencialidad + integridad)

Un analista de riesgo consulta el perfil de un cliente a través de
`ms-cliente`; el experimento materializa dos ataques reales contra el stack
en ejecución — un JWT forjado (confidencialidad) y una alteración del perfil
en tránsito vía `mitmproxy` (integridad) — y mide cuánto tarda el sistema en
**detectar** y en **reaccionar** ante cada uno.

| ASR | Atributo | Objetivo |
|---|---|---|
| **ASR1** — detección | Confidencialidad | detectar la extracción no autorizada en `< 200 ms` |
| **ASR2** — detección | Integridad | detectar la alteración no autorizada en `< 500 ms` |
| **ASR3** — reacción | Confidencialidad | notificar al analista en `< 5 s` desde la detección |
| **ASR4** — reacción | Integridad | notificar al analista en `< 5 s` desde la detección |

### Arquitectura

Cinco microservicios Python (Flask + Celery) sobre un **Event Bus** RabbitMQ
propio (`solventa-seguridad`, distinto del de `backend/`), con un
`mitmproxy` siempre interpuesto entre `ms-cliente` y `ms-riesgo`:

```
analista ─POST /perfil-riesgo─▶ ms-cliente ─validar-usuario─▶ ms-identidad
                                     │
                                     ▼
                                mitmproxy ──▶ ms-riesgo
                          (altera una fracción de las respuestas,
                                MITM_ATTACK_RATIO)
                                     │
                     ValidadorIntegridad (hash HMAC) en ms-cliente
                                     │
      ReporteSesionAccion / ReporteExtraccionPerfil / IntegridadFallida
                                     ▼
                                 ms-audit  ──incidente_seguridad──▶ ms-notificaciones
                       (detector heurístico:                (notifica al analista,
                        BOLA + comportamiento)                mide ASR3/ASR4)
```

- **`ms-identidad`** — identifica, autentica y autoriza. Contiene una
  vulnerabilidad **deliberada** de tipo BOLA (no valida que el `customer_id`
  del token coincida con el solicitado) que el ataque de confidencialidad
  explota; la detección corre aguas abajo, en `ms-audit`.
- **`ms-cliente`** — único punto de entrada HTTP síncrono del flujo; orquesta
  `ms-identidad` → `ms-riesgo` y verifica el hash de integridad del perfil
  recibido antes de responder.
- **`ms-riesgo`** — custodia el perfil de riesgo (dato sensible/PII) y lo
  firma con `hmac-sha256` (`GeneradorIntegridad`).
- **`ms-audit`** — único servicio que **emite** incidentes de seguridad;
  correlaciona los eventos por `request_id`, clasifica intrusiones con un
  detector heurístico (BOLA determinista + anomalía de comportamiento
  `país`/`device` bayesiana) y mide ASR1/ASR2.
- **`ms-notificaciones`** — consume el incidente, lo registra (evidencia
  end-to-end, notificación real al analista fuera de alcance) y mide
  ASR3/ASR4.
- **Infra**: RabbitMQ (broker propio), 3 PostgreSQL (uno por servicio con
  estado), `mitmproxy` (segmento de red comprometido simulado), y — en el
  perfil `experimento` — OTel Collector + Prometheus + Grafana, con Locust
  como generador de tráfico de ataque.

El detalle completo (contratos de eventos, detector heurístico, decisiones de
alcance aún abiertas) está en [`seguridad/README.md`](seguridad/README.md).

### Estado

| Componente | Estado |
|---|---|
| Estructura + `docker-compose` + imagen base propia | ✅ |
| `ms-identidad` (`ValidarUsuario` + BOLA deliberado) | ✅ |
| `ms-cliente` (orquestación + `ValidadorIntegridad` + productor `IntegridadFallida`) | ✅ |
| `ms-riesgo` (`SolicitarPerfil` + `GeneradorIntegridad`) | ✅ |
| `mitmproxy` (altera perfiles en tránsito) | ✅ |
| `ms-audit` (detector heurístico + clasificación + incidente) | ✅ |
| `ms-notificaciones` (notifica al analista) | ✅ |
| Observabilidad (OTel Collector + Prometheus + Grafana) | ✅ pipeline + dashboard por ASR |
| `seed/` (datos dummy con Faker, 3 bases) | ✅ |
| `experimento/` (JWT forjado + mitmproxy + Locust) | ✅ |

### Puesta en marcha rápida

Requisitos: Docker Desktop con Compose v2. Todo se ejecuta desde `seguridad/`.

```sh
cd seguridad
sh build-base.sh
```

El script crea `.env` desde `.env.example`, construye la imagen base
`solventa/security-flask-base` y levanta el stack (incluye el `seed`, que
puebla las 3 bases con datos dummy y termina).

```sh
# forjar un token de CLI-0001 y pedir el perfil de otro cliente (CLI-0007) — ver seguridad/ms-identidad/README.md
python3 -c "import jwt; print(jwt.encode({'customer_id': 'CLI-0001'}, 'change-me', algorithm='HS256'))"
curl -s -XPOST http://localhost:6002/perfil-riesgo \
  -H 'Content-Type: application/json' \
  -d '{"token":"<token>","customer_id":"CLI-0007"}'
```

Detener: `docker compose down` (o `down -v` para también borrar los datos de
las 3 bases).

### Ejecutar el experimento (con métricas)

1. Activar la telemetría en `seguridad/.env`: `OTEL_SDK_DISABLED=false`,
   `OTEL_TRACES_EXPORTER=otlp`, `OTEL_METRICS_EXPORTER=otlp`.
2. Levantar el stack completo (añade `otel-collector`, `prometheus`,
   `grafana`): `docker compose --profile experimento up -d --build`.
3. Ejercitar los 4 ASR — mitmproxy ya está en el camino por defecto
   (`MITM_ATTACK_RATIO=0.2`, ~20 % de los perfiles alterados), así que **una
   sola corrida de Locust** en http://localhost:8089 ejercita confidencialidad
   (tráfico BOLA/anómalo) e integridad (fracción alterada) a la vez; o usar
   `experimento/forjar_token.py` para un disparo puntual de confidencialidad.
4. Observar el dashboard **Solventa · Experimento de seguridad** en
   http://localhost:3001: detección (ASR1/ASR2) vs. su umbral y notificación
   (ASR3/ASR4) vs. 5 s, con el `% que cumple` de cada uno.

Evidencia sin Grafana: `docker compose logs -f ms-audit ms-notificaciones` y
`GET http://localhost:6004/incidentes`. Pasos y escenarios detallados en
[`seguridad/experimento/README.md`](seguridad/experimento/README.md).

## Flujo de trabajo

- Ramas `feature/*` desde `develop`; Pull Request hacia `develop`; `main` se
  reserva para versiones estables.
- Conventional Commits en español (`fix:`, `feat(<área>): …`).
