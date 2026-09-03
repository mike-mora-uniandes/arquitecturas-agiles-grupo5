# arquitecturas-agiles-grupo5

Repositorio de trabajo del **Grupo 5** para la asignatura **Arquitecturas Ágiles** (MISO).

Contiene el backend del experimento de **disponibilidad** del proyecto **Solventa**:
tres microservicios que colaboran para evaluar el perfil de riesgo de un cliente
aplicando las tácticas *Exception Detection*, *Retry* y *Exception Handling*.

## Estructura del repositorio

```
.
├── README.md
└── backend/
    ├── README.md                 # detalle operativo del backend
    ├── docker-compose.yml        # orquesta los 6 servicios
    ├── build-base.sh             # construye la imagen base y levanta el stack
    ├── .env.example              # plantilla de configuración
    │
    ├── base-image/               # imagen general Flask/Python (solventa/flask-base)
    ├── redis/                    # imagen Redis (caché de datos externos)
    │
    ├── ms-riesgos/               # MS Riesgos — punto de entrada REST
    ├── ms-perfil-riesgo/         # MS PerfilRiesgo — cálculo + tácticas de disponibilidad
    ├── ms-notificaciones/        # MS Notificaciones — entrega del resultado
    │
    ├── rabbitmq/                 # broker de mensajería (config propia, pendiente)
    ├── wiremock/                 # simulación de Open Data / Open Finance (pendiente)
    └── observabilidad/           # OpenTelemetry + Grafana (pendiente)
```

Cada microservicio sigue el mismo layout (referencia: `backend/ms-perfil-riesgo/`):

| Carpeta / archivo | Rol |
|---|---|
| `Dockerfile` | imagen del servicio; `FROM solventa/flask-base` |
| `requirements.txt` | dependencias propias sobre la imagen base |
| `run.sh` | arranque (API gunicorn; worker Celery cuando haya lógica) |
| `app.py` | app Flask + `/health` |
| `config.py` | configuración desde variables de entorno |
| `extensiones.py` | `db`, `celery_app` |
| `modelos/` | modelos SQLAlchemy |
| `vistas/` | recursos Flask-RESTful |
| `logica/` | reglas de negocio |
| `tareas/` | tareas Celery (productores/consumidores del broker) |
| `tests/` | pruebas |

## Stack

- Python 3.12 · Flask · Flask-RESTful · SQLAlchemy · Celery
- RabbitMQ (broker AMQP) · Redis (caché) · Wiremock (fuentes externas simuladas)
- Docker + Docker Compose

Las versiones de Flask / SQLAlchemy / marshmallow están alineadas con el
repositorio de referencia `MISW4201-202614-Backend-Grupo08`.

## Ejecución

Requisitos: Docker Desktop en ejecución con Compose v2 (`docker compose version`).

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

Ambos scripts hacen lo mismo:

1. crea `.env` a partir de `.env.example` si no existe,
2. construye la imagen base `solventa/flask-base` (paso previo obligatorio; no es
   un servicio de Compose),
3. levanta el stack con `docker compose up -d --build` y muestra el estado.

### Servicios

| Servicio | URL | Descripción |
|---|---|---|
| ms-riesgos | http://localhost:5001 | punto de entrada REST |
| ms-perfil-riesgo | http://localhost:5002 | cálculo del perfil de riesgo |
| ms-notificaciones | http://localhost:5003 | entrega del resultado |
| RabbitMQ | http://localhost:15672 | consola de administración (`guest` / `guest`) |
| Redis | `localhost:6379` | caché de datos externos |
| Wiremock | http://localhost:8080 | Open Data / Open Finance simulados |

### Verificación

```sh
curl http://localhost:5001/health
curl http://localhost:5002/health
curl http://localhost:5003/health
```

Cada uno responde `{"servicio": "...", "estado": "ok"}`.

### Detener

```sh
cd backend
docker compose down
```

## Estado actual

Entrega de **estructura base**: los servicios construyen, arrancan y responden su
`/health`. Todavía **no** hay lógica de negocio ni implementación de las tácticas
ASR1 / ASR2 / ASR3.

## Flujo de trabajo

- Ramas de trabajo desde `develop` con prefijo `feature/`.
- Pull Request hacia `develop`; `main` se reserva para versiones estables.
