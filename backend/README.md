# Backend Solventa — microservicios

Backend del experimento de disponibilidad de Solventa. `ms-perfil-riesgo` ya
implementa las tácticas ASR1/ASR2/ASR3; `ms-riesgos` y `ms-notificaciones` son
andamiaje (responden `/health`).

## Requisitos

- Docker con Compose v2 (`docker compose version`)
- Docker Desktop en ejecución

## Ejecutar

Desde **PowerShell** (Windows):

```powershell
cd backend
./build-base.ps1
```

Desde **Git Bash / Linux / macOS**:

```sh
cd backend
sh build-base.sh
```

El script (`.ps1` o `.sh`):

1. crea `.env` desde `.env.example` si no existe,
2. construye la imagen general `solventa/flask-base` (paso previo obligatorio,
   **no** es un servicio de compose),
3. levanta el stack con `docker compose up -d --build` y muestra el estado.

Detener: `docker compose down` (o `docker compose --profile experimento down -v`).

### Modo experimento

```sh
docker compose --profile experimento up
```

Añade `redis-seed` (repuebla el caché), `otel-collector`, `prometheus`,
`grafana` (:3000) y `locust` (:8089). Para emitir métricas hay que poner en
`.env`: `OTEL_SDK_DISABLED=false`, `OTEL_TRACES_EXPORTER=otlp`,
`OTEL_METRICS_EXPORTER=otlp`.

## Servicios

| Servicio | Puerto(s) | Estado |
|---|---|---|
| `ms-riesgos` | 5001 | andamiaje (`/health`) |
| `ms-perfil-riesgo` | 5002 | **ASR1/ASR2/ASR3 implementadas** (API + worker) |
| `ms-notificaciones` | 5003 | andamiaje (`/health`) |
| `rabbitmq` | 5672 / 15672 | imagen oficial |
| `redis` | 6379 | imagen propia, `noeviction`, efímero |
| `wiremock` | 8080 | mappings por `customer_id` (`./wiremock/mappings`) |
| `redis-seed` | — | perfil `experimento`, one-shot |
| `otel-collector` / `prometheus` / `grafana` / `locust` | 4318·9464 / 9090 / 3000 / 8089 | perfil `experimento` |

## Layout de un microservicio

```
<ms>/
├── Dockerfile          # FROM solventa/flask-base
├── requirements.txt    # extras del servicio (+ requirements-dev.txt para tests)
├── run.sh              # arranque (gunicorn; + worker Celery en ms-perfil-riesgo)
├── app.py              # Flask app + /health
├── config.py           # configuración desde variables de entorno
├── extensiones.py      # celery_app (+ redis_client en ms-perfil-riesgo)
├── vistas/  logica/  tareas/  tests/
└── modelos/            # modelos SQLAlchemy   (solo si el servicio persiste)
```

## Pendiente

- Implementación de `ms-riesgos` (endpoint REST → publica `perfil.evaluate_profile`)
  y `ms-notificaciones` (consume `profile.result.q`); ajustar `experimento/locustfile.py`.
- Confirmar con el equipo el contrato propuesto (mensajes, topología RabbitMQ,
  esquema de Wiremock, nombres OTel).
