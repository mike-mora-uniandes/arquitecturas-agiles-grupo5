# ms-riesgos

Punto de entrada del flujo. API HTTP que recibe la solicitud del analista,
genera el `correlation_id` de trazabilidad y **publica la solicitud de forma
asíncrona** en RabbitMQ; no espera el resultado.

Solo API (gunicorn, `run.sh`), **sin worker Celery** propio: publica con
`celery_app.send_task(...)`. Sin persistencia y sin endpoint de health.

## Endpoint

`POST /evaluations`  (alias equivalente: `POST /riesgos/evaluar`)

### Petición

```json
{
  "customer_id": "C001",
  "requested_by": "analista-07",
  "scenario": "E0"
}
```

| Campo | Obligatorio | Notas |
|---|---|---|
| `customer_id` | **sí** | también selecciona el escenario de Wiremock. Se acepta el alias `cliente_id` |
| `requested_by` | no | id del analista. Alias `analista_id` |
| `scenario` | no | etiqueta informativa de la corrida de carga (`E0`…`E5`) |
| `tipo_evaluacion`, `detalles` | no | se arrastran en la solicitud publicada |

### Respuesta `202 Accepted`

```json
{
  "correlation_id": "b1e...-uuid",
  "customer_id": "C001",
  "estado": "aceptado",
  "mensaje": "Solicitud encolada correctamente"
}
```

`400` si el cuerpo no es un objeto JSON o falta `customer_id`.

## Qué publica

`tareas/publicacion.py` → `celery_app.send_task`:

| | valor |
|---|---|
| nombre de la tarea | `perfil.evaluate_profile` (la consume `ms-perfil-riesgo`) |
| argumento único | la solicitud completa (dict), con `correlation_id` y `solicitado_en` (ISO-8601 UTC) |
| exchange / routing key | `solventa` (topic) / `profile.request` |
| `retry=True` | reintenta la publicación ante fallo transitorio del broker |

El enrutado efectivo es por **routing key**; la cola de trabajo real
(`profile.request.q`) la declara `ms-perfil-riesgo`.

> Nota: `config.py` de este servicio define `REQUEST_QUEUE=profile.request.queue`
> / `RESULT_QUEUE=profile.result.queue`, con nombres distintos a los de los otros
> dos servicios (`*.q`). Hoy es inocuo porque `ms-riesgos` no consume ninguna
> cola y publica por routing key, pero conviene unificarlo si en el futuro este
> servicio declara o consume colas.

## Variables de entorno

`RABBITMQ_URL`, `RABBITMQ_EXCHANGE` (`solventa`), `REQUEST_ROUTING_KEY`
(`profile.request`), `LOG_LEVEL`. Ver `../.env.example`.

## Ejecutar y probar

Dentro del stack:

```sh
curl -s -XPOST http://localhost:5001/evaluations \
  -H 'Content-Type: application/json' \
  -d '{"customer_id":"C001","requested_by":"analista-07"}'
```

Pruebas unitarias (3, `pytest`, sin broker — `send_task` mockeado):

```sh
cd ms-riesgos
pip install -r requirements.txt        # + la imagen base para Flask/Celery
python -m pytest tests
```

## Dependencias

Sobre `solventa/flask-base`: `celery==5.3.6` (fija una versión distinta a la
`5.4.0` de la imagen base; solo se usa como productor Kombu).
