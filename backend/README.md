# Backend Solventa — microservicios

Estructura base de los microservicios para el experimento de disponibilidad de
Solventa. **Aún no incluye lógica de negocio**: cada servicio arranca y responde
su `/health`, nada más.

## Requisitos

- Docker con Compose v2 (`docker compose version`)
- Docker Desktop en ejecución

## Ejecutar

```sh
cd backend
sh build-base.sh
```

`build-base.sh`:

1. crea `.env` desde `.env.example` si no existe,
2. construye la imagen general `solventa/flask-base` (paso previo obligatorio,
   **no** es un servicio de compose),
3. levanta el stack con `docker compose up -d --build` y muestra el estado.

Detener:

```sh
docker compose down
```

## Servicios

| Servicio | Puerto(s) | Dueño | Estado en esta entrega |
|---|---|---|---|
| `ms-riesgos` | 5001 | Lore | andamiaje (`/health`) |
| `ms-perfil-riesgo` | 5002 | Jeffrey | estructura base, **sin** lógica ASR |
| `ms-notificaciones` | 5003 | Michael | andamiaje (`/health`) |
| `rabbitmq` | 5672 / 15672 | Michael | imagen oficial |
| `redis` | 6379 | Jeffrey | imagen propia (`./redis`) |
| `wiremock` | 8080 | Lore | imagen oficial, sin mappings |

Comprobar que todo está arriba:

```sh
curl http://localhost:5001/health
curl http://localhost:5002/health
curl http://localhost:5003/health
```

## Layout de un microservicio

Plantilla común (referencia: `ms-perfil-riesgo/`):

```
<ms>/
├── Dockerfile          # FROM solventa/flask-base
├── .dockerignore
├── requirements.txt    # extras del servicio sobre la imagen base
├── run.sh              # arranque (gunicorn; worker Celery cuando exista lógica)
├── app.py              # Flask app + /health
├── config.py           # configuración desde variables de entorno
├── extensiones.py      # db, celery_app
├── modelos/            # modelos SQLAlchemy        (solo si el servicio persiste)
├── vistas/             # recursos Flask-RESTful
├── logica/             # reglas de negocio
├── tareas/             # tareas Celery (consumidores/publicadores del broker)
└── tests/
```

## Pendiente (otros integrantes)

- `rabbitmq/`, `wiremock/`, `observabilidad/` (OpenTelemetry + Grafana)
- Lógica de las tácticas ASR1 / ASR2 / ASR3 en `ms-perfil-riesgo/logica/`
- Implementación de `ms-riesgos` y `ms-notificaciones`
