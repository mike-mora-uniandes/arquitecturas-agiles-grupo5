# ms-notificaciones

Informa al analista de riesgo los incidentes que detecta `ms-audit` — cierra
el ciclo de **reacción** de ASR3 (confidencialidad) y ASR4 (integridad). API +
worker Celery en el mismo contenedor (`run.sh`, `wait -n`).

**Comportamiento:** consume `NotificacionIncidenteSeguridad`
(`tareas/entrega.py`), lo registra como log estructurado (evidencia
end-to-end, mismo criterio que el experimento 1) y mide el tiempo de reacción.

## Qué consume

| | valor |
|---|---|
| tarea | `notificaciones.notificar_incidente` |
| cola | `notificaciones.incidente.q` |
| routing key | `audit.incidente_seguridad` |
| exchange | `solventa-seguridad` (topic) |

## Métrica emitida (OTel → Prometheus)

| instrumento | tipo | ASR |
|---|---|---|
| `tiempo_notificacion_ms{tipo}` | histogram | ASR3/ASR4 (<5 s) |
| `solventa_seguridad_asr_notificacion_within_total{tipo,pass}` | counter | ASR3/ASR4 |

**Medición:** `t0` = `detectado_en` que viene en el incidente (momento en que
`ms-audit` lo clasificó); `t1` = momento en que llega aquí. La resta es el
tiempo de reacción. Se etiqueta por `tipo` (`confidencialidad` = ASR3,
`integridad` = ASR4).

> **Reloj:** todas las marcas son UTC. El experimento corre en un solo host
> (Docker Compose), así que los relojes de los contenedores comparten el del
> kernel y la resta entre servicios es comparable. En un despliegue multi-host
> habría que sincronizar con NTP o medir por tramos.

Pendiente (fuera de alcance del experimento, igual que en el experimento 1):
mecanismo real de notificación (email/webhook) — hoy el log es evidencia
suficiente.
