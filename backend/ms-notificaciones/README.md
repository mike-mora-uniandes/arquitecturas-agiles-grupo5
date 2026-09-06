# ms-notificaciones

Último eslabón del flujo. Consume el `ProfileEvaluationResult` que publica
`ms-perfil-riesgo` y lo **registra en el log**. Para el experimento de
disponibilidad eso es suficiente: el log es la evidencia end-to-end de que el
Event Bus entrega el resultado al analista sin errores. La notificación real
(webhook, endpoint de consulta, etc.) queda **fuera de alcance** — todas las
tácticas ASR ocurren aguas arriba, en `ms-perfil-riesgo`.

API Flask **sin rutas** + worker Celery en el mismo contenedor (`run.sh`,
`wait -n`), igual patrón que `../ms-perfil-riesgo/`. Sin persistencia, sin
health.

## Qué consume

| | valor |
|---|---|
| tarea Celery | `notificaciones.deliver_result` (`Config.RESULT_TASK_NAME`) |
| cola | `profile.result.q` (clásica durable, la declara este servicio en `extensiones.py`) |
| exchange / routing key | `solventa` (topic) / `profile.result` |
| DLX | `solventa.dlx` con rk `profile.result.dead` (el exchange y `profile.result.dead.q` los declara `ms-perfil-riesgo`) |
| config Celery | `task_acks_late=True`, `worker_prefetch_multiplier=1`, `--concurrency=1` |

## Flujo (`tareas/entrega.py`)

`ProfileEvaluationResult` → `log.info(...)` → `ack`.

Con `task_acks_late=True` el `ack` se hace al terminar la tarea; si el worker
muere antes, RabbitMQ reentrega el mensaje.

## Variables de entorno (ver `../.env.example`)

`RABBITMQ_URL`, `RABBITMQ_EXCHANGE` (`solventa`), `RABBITMQ_DLX` (`solventa.dlx`),
`RESULT_QUEUE` (`profile.result.q`), `RESULT_ROUTING_KEY` (`profile.result`),
`RESULT_TASK_NAME` (`notificaciones.deliver_result`), `RETRY_MAX` (disponible por
si se añade reintento propio; hoy no se usa), `LOG_LEVEL`.

## Ver el resultado en una corrida

```sh
docker compose logs -f ms-notificaciones | grep "ProfileEvaluationResult recibido"
```

## Notas

- `requirements.txt` está vacío: el servicio no necesita dependencias más allá de
  `solventa/flask-base`. Si en el futuro se quisiera una notificación real
  (webhook, cola de salida, reintento propio + DLQ), se añadirían aquí.
