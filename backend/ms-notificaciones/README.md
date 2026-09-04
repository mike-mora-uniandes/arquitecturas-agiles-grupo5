# ms-notificaciones

Consume `ProfileEvaluationResult` (tarea Celery `notificaciones.deliver_result`,
cola `profile.result.q`) publicado por `ms-perfil-riesgo`. No expone endpoints
HTTP; es API (sin rutas) + worker Celery en el mismo contenedor (`run.sh`,
`wait -n`), igual que `../ms-perfil-riesgo/`.

> Por ahora el consumer solo **loguea** el resultado recibido — sirve como
> métrica de validación end-to-end del Event Bus. El mecanismo real de
> notificación al analista de riesgo (webhook, endpoint de consulta, etc.)
> todavía lo debe confirmar el equipo.

## Flujo (`tareas/entrega.py`)

`ProfileEvaluationResult` → log (`logging`) → ack automático (Celery,
`task_acks_late=True`: si el worker muere antes de terminar la tarea, RabbitMQ
reencola el mensaje).

Pendiente:
- Reintento (máx. `RETRY_MAX`) y envío a la Dead-Letter Queue.
- Mecanismo real de notificación al analista de riesgo.
- Imagen RabbitMQ (`../rabbitmq/`).
