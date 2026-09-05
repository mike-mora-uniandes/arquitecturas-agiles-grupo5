# RabbitMQ

Broker AMQP del **Event Bus** entre los tres microservicios. Hoy
`docker-compose.yml` usa la imagen oficial `rabbitmq:3.13-management-alpine`
directamente (sin `Dockerfile` propio).

- AMQP: `5672` · Consola de administración: `15672` (usuario/clave `guest` / `guest`)
- Límites en compose: `1.0` CPU / `512M`

## Topología (la declaran los microservicios al arrancar)

No hay `definitions.json`: cada servicio declara lo que necesita vía
Celery/Kombu.

| Elemento | Nombre | Tipo | Declara |
|---|---|---|---|
| Exchange principal | `solventa` | `topic`, durable | los 3 servicios (`extensiones.py`) |
| Cola de solicitudes | `profile.request.q` | clásica durable | `ms-perfil-riesgo` (`task_queues`) |
| Cola de resultados | `profile.result.q` | clásica durable | `ms-notificaciones` (`task_queues`) |
| Dead-letter exchange | `solventa.dlx` | `topic`, durable | `ms-perfil-riesgo` (`topologia.py`, en `worker_ready`) |
| Colas muertas | `profile.request.dead.q`, `profile.result.dead.q` | durables, sin TTL | `ms-perfil-riesgo` (`topologia.py`) |

Routing keys: `profile.request` (solicitud), `profile.result` (resultado),
`<rk>.dead` hacia el DLX.

Argumentos de las colas de trabajo:
`x-dead-letter-exchange=solventa.dlx`, `x-dead-letter-routing-key=<rk>.dead`.

### Por qué colas **clásicas** y no *quorum*

Celery 5.4 aplica QoS **global** al canal; las colas quorum solo aceptan QoS por
consumidor y rechazan la conexión (`NOT_IMPLEMENTED - does not support global
qos`). Una cola clásica durable + `delivery_mode=2` + DLX también sobrevive al
reinicio de RabbitMQ en un nodo único. Con Celery ≥ 5.5 y
`worker_detect_quorum_queues` se podría migrar a quorum + `x-delivery-limit`.

### Semántica de entrega

- `ms-perfil-riesgo`: `task_acks_late=true`, `worker_prefetch_multiplier=1`
  (prefetch 1), `ack` manual tras publicar el resultado. Mensaje ilegible o
  excepción no controlada → `Reject(requeue=false)` → DLQ (sin reencolado).
- Los productores (`ms-riesgos`, `ms-perfil-riesgo`) publican con `retry=True`
  en `send_task`: reintentan la publicación ante un fallo transitorio del broker.

## Comprobaciones útiles

```sh
# colas y su profundidad
docker compose exec rabbitmq rabbitmqctl list_queues name messages consumers

# ¿algo cayó a la DLQ? (debe ser 0 en una corrida sana)
docker compose exec rabbitmq rabbitmqctl list_queues name messages | grep dead
```

Consola web: http://localhost:15672 → *Queues*.

## Si se necesita configuración propia

1. añadir aquí `Dockerfile`, `definitions.json` y/o `enabled_plugins`;
2. en `docker-compose.yml` cambiar el servicio `rabbitmq` de `image:` a
   `build: ./rabbitmq`.
