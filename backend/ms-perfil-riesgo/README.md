# ms-perfil-riesgo

Estructura base. El servicio construye, arranca (API + worker Celery en el mismo
contenedor) y responde `GET /health`. **Aún sin lógica de ASR1/ASR2/ASR3.**

- Sin persistencia local: el perfil vive en Redis y se publica al broker.
- `GET /profiles/<customer_id>` → `501` (fuera de alcance del experimento).
- `run.sh` levanta worker + gunicorn; si cualquiera muere, el contenedor cae.

## Flujo objetivo (a implementar)

`ProfileEvaluationRequest` (RabbitMQ) → idempotencia (`processed:{correlation_id}`)
→ `ConsultaPerfil` (Open Data + Open Finance concurrentes)
→ `deteccion_excepciones` (ASR1) → retry con `tenacity` (ASR3)
→ `manejo_excepciones` + `cache_externos` (ASR2) → `calculo_perfil`
→ publicar `ProfileEvaluationResult`.

| Componente (`logica/`) | Responsabilidad | ASR |
|---|---|---|
| `deteccion_excepciones.py` | clasificar fallo de fuente externa (< 700 ms) | ASR1 |
| `consulta_perfil.py` | orquestar Open Data / Open Finance | ASR1/ASR3 |
| `calculo_perfil.py` | `score` / `category` | — |
| `manejo_excepciones.py` | escalar al agotar reintentos | ASR2 |
| `cache_externos.py` | `GET`/`SET` en Redis (< 100 ms) | ASR2 |

Contratos de mensajes, topología RabbitMQ, esquema de Wiremock y spans OTel:
pendientes de acordar con el equipo.
