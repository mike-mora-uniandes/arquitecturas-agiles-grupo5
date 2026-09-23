# ms-audit

Consolida los eventos de auditoría, **clasifica patrones de intrusión** y
publica el incidente. API + worker Celery en el mismo contenedor (`run.sh`,
`wait -n`), igual patrón que `ms-perfil-riesgo` del experimento 1.

**Propósito:** detectar sin que pase de forma silenciosa una extracción no
autorizada del perfil (confidencialidad, ASR1) o una alteración del perfil
(integridad, ASR2), y disparar la notificación al analista.

## Qué consume / qué produce

| | valor |
|---|---|
| consume | `audit.registrar_sesion_accion` (de `ms-identidad`) · `audit.registrar_extraccion_perfil` (de `ms-riesgo`) · `audit.registrar_integridad_fallida` (de `ms-cliente`) |
| colas | `audit.sesion_accion.q`, `audit.extraccion_perfil.q`, `audit.integridad_fallida.q` |
| exchange | `solventa-seguridad` (topic) |
| produce | `audit.incidente_seguridad` → tarea `notificaciones.notificar_incidente` |
| BD | PostgreSQL `audit`: `historial_conexion`, `historial_registros_usuario`, `incidentes` |
| API | `GET /incidentes` (últimos 100, evidencia) · `GET /salud` |

## Detección de confidencialidad (ASR1) — detector heurístico

Cada request es una extracción: su `ReporteSesionAccion` y su
`ReporteExtraccionPerfilRiesgoCliente` comparten un `request_id`
(`logica/clasificador_intrusiones.py` los empareja por ese id, exacto). La
decisión la toma el **detector heurístico** (`logica/detector.py`), que combina
dos señales:

1. **BOLA** (determinista, peso máximo) — sesión validada donde
   `customer_id_token != customer_id_solicitado` (la vulnerabilidad deliberada
   de `ms-identidad`: un token válido para un cliente usado para extraer el
   perfil de otro).
2. **Comportamiento** (probabilístico) — qué tan improbable es el `país`/`device`
   de la request dado el **historial NO anómalo del actor**:

   ```
   P(país)   = (veces(país)   + α) / (N + α·(distintos_país   + 1))
   P(device) = (veces(device) + α) / (N + α·(distintos_device + 1))
   P(normal) = P(país)·P(device)     ;  score = 1 − P(normal)
   intrusión  si  score ≥ DETECCION_UMBRAL
   ```

El "normal" se **deriva del propio `historial_conexion`** (no de una tabla
aparte): las conexiones marcadas `anomala = true` se **excluyen** para que el
tráfico del atacante no envenene la línea base. El suavizado de Laplace (α)
evita ceros duros y sobre-marcar con historial escaso; con menos de
`DETECCION_MIN_MUESTRAS` conexiones del actor solo aplica BOLA. Esto detecta el
caso de un **usuario legítimo desde ubicación/device inusual** (que un BOLA no
cubre) y tolera **patrones múltiples legítimos** (p. ej. un cliente que alterna
dos países), a diferencia de un match exacto.

**Arranque en frío:** el historial normal inicial lo llena el `seed/` en
`historial_conexion`, y `ms-audit` lo **auto-siembra** como respaldo si la tabla
está vacía (`AUTOSEED_*`), sin acoplar la seed a su esquema.

**Medición ASR1:** `t0` = `reportado_en` de la extracción; `t1` = momento de la
clasificación en `ms-audit`. La resta es la latencia del camino asíncrono
(publicar → broker → consumir → clasificar) — el punto de incertidumbre del
diseño frente al umbral de 200 ms.

## Detección de integridad (ASR2) — inline en ms-cliente

La detección ocurre en `ms-cliente` (recalcula y compara el hash del perfil).
Como `ms-cliente` no persiste ni notifica, publica el evento **IntegridadFallida**
al broker y `ms-audit` lo centraliza: registra el incidente, emite la métrica
y publica la notificación. Así se mantiene el invariante del diseño *"solo
ms-audit emite incidentes de seguridad"*.

### Contrato del evento IntegridadFallida

`ms-cliente` publica este evento cuando `verificar_hash` falla — ya está
implementado como productor puro (`ms-cliente/tareas/publicacion.py`,
`extensiones.py`), sin worker. Payload:

```python
{
    "customer_id": customer_id_solicitado,
    # latencia medida inline por ms-cliente: desde que se pidió el perfil a
    # ms-riesgo (donde pudo alterarse en tránsito) hasta que falló el hash
    "deteccion_ms": deteccion_ms,
    "detectado_en": "<ISO-8601 UTC>",
    "detalle": "hash de integridad no coincide (manipulación en tránsito)",
}
```

Cola/routing key/tarea (`INTEGRIDAD_*` en `.env.example`) coinciden entre
`ms-cliente` y `ms-audit`.

## Métricas emitidas (OTel → Prometheus)

| instrumento | tipo | ASR |
|---|---|---|
| `tiempo_deteccion_confidencialidad_ms` | histogram | ASR1 (<200 ms) |
| `tiempo_deteccion_integridad_ms` | histogram | ASR2 (<500 ms) |
| `solventa_seguridad_asr1_within_threshold_total{pass}` | counter | ASR1 |
| `solventa_seguridad_asr2_within_threshold_total{pass}` | counter | ASR2 |
| `solventa_seguridad_intrusiones_total{tipo}` | counter | — |

Con `OTEL_SDK_DISABLED=true` (default) los instrumentos son no-op. Cada hijo
del pool prefork recibe su propio `service.instance.id` (ver `telemetria.py` y
la explicación extendida en `backend/ms-perfil-riesgo/telemetria.py`).
