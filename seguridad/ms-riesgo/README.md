# ms-riesgo

Implementado: `SolicitarPerfil` + `GeneradorIntegridad` + publicación de
`ReporteExtraccionPerfilRiesgoCliente`. Productor puro (usa Celery como
cliente, no corre worker — ver `run.sh`).

**Propósito:** custodiar y entregar el perfil de riesgo del cliente (datos
sensibles, PII) junto con evidencia verificable de su integridad, y dejar
registro de cada extracción atendida. Solo accesible por `ms-cliente`, nunca
directamente desde fuera — es el objetivo del ataque de confidencialidad
(ASR1) del experimento.

## `GET /perfiles/<customer_id>`

```json
// Response 200
{
  "customer_id": "CLI-0007",
  "nombre_completo": "Juana Pérez",
  "documento_identidad": "123456",
  "puntaje": 80,
  "categoria": "ALTO",
  "actualizado_en": "2026-01-01T00:00:00+00:00",
  "hash_integridad": "<hmac-sha256 hex>"
}

// Response 404
{ "error": "perfil 'CLI-9999' no encontrado" }
```

`hash_integridad` se calcula con `hmac-sha256` sobre el resto del payload
(orden de llaves normalizado con `json.dumps(sort_keys=True)`) y
`Config.INTEGRITY_SECRET`. `ms-cliente` (`ValidadorIntegridad`) recalcula el
mismo hash sobre el payload recibido y lo compara — ver
`../ms-cliente/logica/validador_integridad.py`.

## Modelo de datos (`logica/modelos.py`)

`perfiles_riesgo(customer_id PK, nombre_completo, documento_identidad,
puntaje, categoria, actualizado_en)` — poblado por `../seed/`. `puntaje` es
0-100 con los mismos cortes que
`backend/ms-perfil-riesgo/logica/calculo_perfil.py` (BAJO <34, MEDIO 34-66,
ALTO >66), traducidos al español; es un valor dummy, no hay cálculo real de
riesgo en este experimento.

## Qué publica (`tareas/publicacion.py`)

| | valor |
|---|---|
| tarea Celery consumida por | `audit.registrar_extraccion_perfil` (`Config.EXTRACCION_TASK_NAME`) |
| exchange / routing key | `solventa-seguridad` (topic) / `riesgo.extraccion_perfil` |

Se publica en **cada** extracción atendida (perfil encontrado), sin firma:
el punto de sensibilidad del experimento es el perfil que viaja hacia
`ms-cliente`, no este canal interno de auditoría (ver `../README.md`). Lleva
el `request_id` que `ms-cliente` propaga en el header `X-Request-Id` de la
request GET, para que `ms-audit` empareje esta extracción con su sesión.

## Variables de entorno (ver `../.env.example`)

`RIESGO_DATABASE_URL`, `INTEGRITY_SECRET`, `RABBITMQ_URL`,
`RABBITMQ_EXCHANGE`, `EXTRACCION_QUEUE`, `EXTRACCION_ROUTING_KEY`,
`EXTRACCION_TASK_NAME`, `LOG_LEVEL`.

## Pruebas

```sh
cd ms-riesgo
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest tests
```

Sin BD ni broker reales: `test_vistas_riesgo.py` usa SQLite en memoria,
`test_publicacion.py` mockea `send_task`, `test_generador_integridad.py`
cubre que el hash es determinista/depende de cada campo, y
`test_extensiones.py` cubre el reintento de `esperar_bd` (Postgres puede
tardar en aceptar conexiones tras arrancar — `depends_on` solo espera a que
el contenedor inicie, no a que el servidor esté listo).

Flujo completo end-to-end con `ms-cliente` verificado, y `docker compose up`
depende de que `seed` termine (`service_completed_successfully`) antes de
arrancar, así que los `customer_id` de `../seed/generar_seed.py` (`CLI-0001`…)
ya tienen perfil poblado — ver `../seed/README.md`.
