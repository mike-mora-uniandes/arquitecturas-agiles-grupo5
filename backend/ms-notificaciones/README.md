# ms-notificaciones

**Dueño: Michael.** En esta rama solo está el andamiaje: el servicio construye,
arranca y responde `GET /health`. No hay lógica de negocio.

Pendiente:
- Consumidor del resultado desde RabbitMQ con ack manual (`tareas/`).
- Reintento (máx. `RETRY_MAX`) y envío a la Dead-Letter Queue.
- Notificación al analista de riesgo.
- Imagen RabbitMQ (`../rabbitmq/`).

Espeja el layout de `../ms-perfil-riesgo/`.
