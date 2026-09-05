# Backend Solventa — microservicios

Backend del experimento de disponibilidad de Solventa. `ms-perfil-riesgo` ya
implementa las tácticas ASR1/ASR2/ASR3; `ms-notificaciones` ya consume y
loguea el resultado (Celery); `ms-riesgos` sigue siendo solo andamiaje
(construye y arranca, sin endpoints).

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

Añade `otel-collector`, `prometheus`, `grafana` (:3000) y `locust` (:8089). Para
emitir métricas hay que poner en `.env`: `OTEL_SDK_DISABLED=false`,
`OTEL_TRACES_EXPORTER=otlp`, `OTEL_METRICS_EXPORTER=otlp`.

El caché de Redis se precarga solo: la imagen `solventa/redis` ejecuta
`redis/seed/profiles.redis` al arrancar el contenedor, en modo normal y en
experimento (idempotente, sin servicio aparte).

## Servicios

| Servicio | Puerto(s) | Estado |
|---|---|---|
| `ms-riesgos` | 5001 | andamiaje (sin endpoints) |
| `ms-perfil-riesgo` | 5002 | **ASR1/ASR2/ASR3 implementadas** (worker + `GET /profiles/<id>` → 501) |
| `ms-notificaciones` | 5003 | consume `profile.result.q` y loguea el resultado (Celery); notificación real pendiente |
| `rabbitmq` | 5672 / 15672 | imagen oficial |
| `redis` | 6379 | imagen propia, `noeviction`, efímero, seed al arrancar |
| `wiremock` | 8080 | mappings por `customer_id` (`./wiremock/mappings`) |
| `otel-collector` / `prometheus` / `grafana` / `locust` | 4318·9464 / 9090 / 3000 / 8089 | perfil `experimento` |

## Layout de un microservicio

```
<ms>/
├── Dockerfile          # FROM solventa/flask-base
├── requirements.txt    # extras del servicio (+ requirements-dev.txt para tests)
├── run.sh              # arranque (gunicorn; + worker Celery en ms-perfil-riesgo)
├── app.py              # Flask app (endpoints del servicio, si tiene)
├── config.py           # configuración desde variables de entorno
├── extensiones.py      # celery_app (+ redis_client en ms-perfil-riesgo)
├── vistas/  logica/  tareas/  tests/
└── modelos/            # modelos SQLAlchemy   (solo si el servicio persiste)
```

## Pendiente

- Implementación de `ms-riesgos` (endpoint REST → publica `perfil.evaluate_profile`);
  ajustar `experimento/locustfile.py`.
- `ms-notificaciones`: mecanismo real de notificación al analista de riesgo
  (hoy solo loguea) y envío a la Dead-Letter Queue tras agotar reintentos —
  pendientes de confirmar con el equipo.
- Confirmar con el equipo el contrato propuesto (mensajes, topología RabbitMQ,
  esquema de Wiremock, nombres OTel).
