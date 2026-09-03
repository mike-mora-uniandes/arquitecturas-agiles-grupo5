# ms-riesgos

En esta rama solo está el andamiaje: el servicio construye, arranca y responde
`GET /health`. No hay lógica de negocio.

Pendiente:
- Endpoint REST que recibe la solicitud del analista y genera un correlation ID.
- Publicación asíncrona de `SolicitudEvaluacionPerfil` a RabbitMQ (`tareas/`).
- Imagen Wiremock (`../wiremock/`).

Espeja el layout de `../ms-perfil-riesgo/` (añade `modelos/` solo si necesitas
persistencia).
