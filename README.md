# arquitecturas-agiles-grupo5

Repositorio de trabajo del **Grupo 5** para la asignatura **Arquitecturas
Ágiles** (MISO).

Backend del **experimento de disponibilidad** del proyecto **Solventa**: un
analista de riesgo solicita la evaluación del perfil de un cliente y el flujo
aplica tres tácticas ante fallos de las fuentes externas Open Data / Open
Finance.

| ASR | Táctica | Objetivo |
|---|---|---|
| **ASR1** | *Exception Detection* | detectar el fallo de una fuente en `< 700 ms` |
| **ASR3** | *Retry* | backoff exponencial + jitter, `≤ 3` intentos, `≤ 5 s` totales |
| **ASR2** | *Exception Handling* | degradar con el respaldo de Redis en `< 100 ms` extra, sin error visible al analista |

## Arquitectura

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

## Estado

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

## Estructura del repositorio

```
.
├── README.md                 # este archivo
├── LICENSE
└── backend/                  # todo el backend del experimento
    ├── README.md             # ▶ guía operativa detallada (estructura, ejecución, pruebas)
    ├── DESIGN.md             # decisiones + contratos (local, gitignored)
    ├── docker-compose.yml
    ├── build-base.sh / .ps1
    ├── .env.example
    ├── base-image/           # solventa/flask-base (Flask + Celery + requests + OpenTelemetry)
    ├── ms-riesgos/           # API de entrada                → backend/ms-riesgos/README.md
    ├── ms-perfil-riesgo/     # cálculo + ASR1/ASR2/ASR3      → backend/ms-perfil-riesgo/README.md
    ├── ms-notificaciones/    # consumer del resultado        → backend/ms-notificaciones/README.md
    ├── redis/                # imagen Redis + seed           → backend/redis/README.md
    ├── wiremock/             # Open Data / Open Finance       → backend/wiremock/README.md
    ├── rabbitmq/             # notas del broker              → backend/rabbitmq/README.md
    ├── observabilidad/       # OTel Collector + Prometheus + Grafana → backend/observabilidad/README.md
    └── experimento/          # carga con Locust (matriz E0–E5)  → backend/experimento/README.md
```

Cada subcarpeta de `backend/` tiene su propio `README.md` con el detalle del
componente.

## Puesta en marcha rápida

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

## Flujo de trabajo

- Ramas `feature/*` desde `develop`; Pull Request hacia `develop`; `main` se
  reserva para versiones estables.
- Conventional Commits en español (`fix:`, `feat(<área>): …`).
