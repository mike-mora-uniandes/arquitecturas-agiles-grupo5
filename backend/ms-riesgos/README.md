# ms-riesgos

Microservicio HTTP que recibe solicitudes de evaluación de riesgo y las publica
asíncronamente en RabbitMQ.

## Endpoint disponible

- POST /riesgos/evaluar

## Comportamiento

- Valida que el payload sea JSON y que incluya cliente_id.
- Genera un correlation_id para trazabilidad de la solicitud.
- Publica la solicitud en la cola profile_evaluation_request.
- No expone endpoint de health check.
