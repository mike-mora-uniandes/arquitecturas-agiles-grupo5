# arquitecturas-agiles-grupo5

Repositorio de trabajo del **Grupo 5** para la asignatura **Arquitecturas Ágiles** (MISO).

Backend del experimento de **disponibilidad** del proyecto **Solventa**: un
analista solicita la evaluación del perfil de riesgo de un cliente y el flujo
aplica tres tácticas — *Exception Detection* (ASR1), *Retry* (ASR3) y
*Exception Handling* (ASR2) — ante fallos de las fuentes externas Open Data /
Open Finance.

## Estado

| Componente | Estado |
|---|---|
| Estructura + `docker-compose` + imagen base Flask/Python | ✅ |
| Imagen Redis (caché de respaldo, ASR2) | ✅ |
| **MS PerfilRiesgo — tácticas ASR1 / ASR2 / ASR3** | ✅ implementadas y verificadas E2E |
| Wiremock (mappings por `customer_id`) | ✅ |
| Observabilidad (OTel Collector + Prometheus + Grafana) | ✅ pipeline; faltan dashboards |
| MS Riesgos · MS Notificaciones | ⏳ andamiaje (solo construyen y arrancan) |

El diseño y los contratos pendientes de acordar con el equipo (mensajes,
topología RabbitMQ, esquema de Wiremock, nombres OTel) están en
`backend/DESIGN.md`.

## Estructura del repositorio

```
.
└── backend/
    ├── README.md               # detalle operativo
    ├── DESIGN.md               # decisiones de diseño y contratos
    ├── docker-compose.yml      # 6 servicios core + 4 del perfil 'experimento'
    ├── build-base.sh / .ps1    # construye la imagen base y levanta el stack
    ├── .env.example
    │
    ├── base-image/             # imagen general Flask/Python (solventa/flask-base)
    ├── redis/                  # imagen Redis + redis.conf + entrypoint (seed automático)
    │
    ├── ms-perfil-riesgo/       # cálculo + tácticas de disponibilidad (implementado)
    ├── ms-riesgos/             # punto de entrada REST (andamiaje)
    ├── ms-notificaciones/      # entrega del resultado (andamiaje)
    │
    ├── wiremock/mappings/      # Open Data / Open Finance simulados por customer_id
    ├── observabilidad/         # otel-collector.yaml, prometheus.yml, grafana/
    └── experimento/            # locustfile.py
```

## Stack

- Python 3.12 · Flask · Flask-RESTful · Celery · **tenacity** (retry) · **OpenTelemetry**
- RabbitMQ (broker AMQP) · Redis (caché) · Wiremock (fuentes externas simuladas)
- OpenTelemetry Collector · Prometheus · Grafana · Locust (perfil `experimento`)
- Docker + Docker Compose

Las versiones de Flask / SQLAlchemy / marshmallow están alineadas con el
repositorio de referencia `MISW4201-202614-Backend-Grupo08`.

## Ejecución

Requisitos: Docker Desktop con Compose v2 (`docker compose version`).

```powershell
cd backend
./build-base.ps1        # PowerShell (Windows)
```

```sh
cd backend
sh build-base.sh        # Git Bash / Linux / macOS
```

El script crea `.env` desde `.env.example`, construye `solventa/flask-base`
(paso previo, no es un servicio) y levanta el stack.

### Modo experimento

```sh
docker compose --profile experimento up
```

Añade `otel-collector`, `prometheus`, `grafana` (`:3000`) y `locust` (`:8089`).
Para emitir métricas, en `.env`: `OTEL_SDK_DISABLED=false`,
`OTEL_TRACES_EXPORTER=otlp`, `OTEL_METRICS_EXPORTER=otlp`.

El caché de Redis lo precarga la propia imagen `solventa/redis` al arrancar
(ejecuta `redis/seed/profiles.redis`); no hay servicio de seed aparte.

### Verificación

```sh
# todos los contenedores en 'running'
docker compose ps

# el worker de MS PerfilRiesgo llegó a 'ready'
docker compose logs ms-perfil-riesgo | grep "celery@.* ready"

# pruebas unitarias de MS PerfilRiesgo
docker compose exec ms-perfil-riesgo sh -c \
  "pip install -q -r requirements-dev.txt && python -m pytest -q tests"
```

### Detener

```sh
docker compose down                       # o  --profile experimento down -v
```

## Servicios

| Servicio | Puerto(s) | Descripción |
|---|---|---|
| `ms-riesgos` | 5001 | punto de entrada REST (andamiaje, sin endpoints) |
| `ms-perfil-riesgo` | 5002 | evaluación del perfil + ASR1/ASR2/ASR3 (worker + `GET /profiles/<id>` → 501) |
| `ms-notificaciones` | 5003 | entrega del resultado (andamiaje, sin endpoints) |
| `rabbitmq` | 5672 / 15672 | broker AMQP (consola: `guest` / `guest`) |
| `redis` | 6379 | caché de respaldo (`noeviction`, efímero) |
| `wiremock` | 8080 | Open Data / Open Finance simulados |
| `otel-collector` / `prometheus` / `grafana` / `locust` | 4318 / 9090 / 3000 / 8089 | perfil `experimento` |

## Flujo de trabajo

- Ramas de trabajo desde `develop` con prefijo `feature/`.
- Pull Request hacia `develop`; `main` se reserva para versiones estables.
