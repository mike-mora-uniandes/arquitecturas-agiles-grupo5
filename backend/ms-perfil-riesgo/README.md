# ms-perfil-riesgo

Microservicio de perfil de riesgo. Consume `perfil.evaluate_profile` de
RabbitMQ, aplica las tácticas ASR1/ASR2/ASR3 y publica `ProfileEvaluationResult`.
API + worker Celery en el mismo contenedor (`run.sh`, `wait -n`). Sin persistencia
local: el perfil vive en Redis y se publica al broker.

> La implementación asume el contrato **propuesto** de `../DESIGN.md` §2
> (mensajes, topología RabbitMQ, esquema de Wiremock, nombres OTel). Si el equipo
> lo cambia, se ajusta `config.py` y `mensajes.py`.

## Flujo (`tareas/evaluacion.py`, ver DESIGN.md §1.4)

`ProfileEvaluationRequest` → idempotencia (`processed:{correlation_id}`)
→ `ConsultaPerfil` (Open Data + Open Finance concurrentes)
→ detección (ASR1) → retry con `tenacity`, presupuesto común (ASR3)
→ si ambas OK: `CalculoPerfil` + refresco de caché · si no: enmascaramiento con
caché (ASR2) → publicar resultado → marcar `processed` → `ack`.

| Módulo (`logica/`) | Rol | ASR |
|---|---|---|
| `fuentes_externas.py` | cliente HTTP + validación de esquema | — |
| `deteccion_excepciones.py` | clasifica el fallo (`timeout`/`connection`/`http_5xx`/`anomalous`) | ASR1 |
| `consulta_perfil.py` | llamadas concurrentes + retry + presupuesto | ASR1 / ASR3 |
| `calculo_perfil.py` | `score` / `category` | — |
| `manejo_excepciones.py` | escala a caché, arma resultado degradado | ASR2 |
| `cache_externos.py` | `GET`/`SET` `profile:{customer_id}` | ASR2 |

`telemetria.py` — spans `profile.*` y métricas `solventa_profile_*` (§2.4).
`topologia.py` — declara el dead-letter exchange y sus colas al arrancar.

## Pruebas

```sh
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest tests
```

## Variables de entorno

Ver `backend/.env.example`. Parámetros de tácticas: `DETECTION_TIMEOUT_MS`,
`RETRY_MAX`, `RETRY_BACKOFF_BASE_MS`, `RETRY_BUDGET_MS`, `CACHE_TTL_S`,
`CACHE_ASR2_THRESHOLD_MS`, `PROCESSED_TTL_S`, `CELERY_CONCURRENCY`.
