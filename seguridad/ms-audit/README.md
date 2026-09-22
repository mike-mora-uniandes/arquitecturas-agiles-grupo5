# ms-audit

Andamiaje: el servicio construye y arranca, sin lógica de negocio todavía.
API + worker Celery en el mismo contenedor (`run.sh`, `wait -n`), igual
patrón que `ms-perfil-riesgo` del experimento 1.

**Propósito final:** consolidar los eventos de auditoría y clasificar los
patrones de acceso que constituyen intrusiones no autorizadas con riesgo de
divulgación indebida de datos (ASR1) o alteración indebida del perfil (ASR2).

**Comportamiento esperado:** consume del Event Bus `ReporteSesionAccion`
(de `ms-identidad`) y `ReporteExtraccionPerfilRiesgoCliente` (de `ms-riesgo`),
los registra (`HistorialConexion`, `HistorialRegistrosUsuario`) y los pasa por
`logica/clasificador_intrusiones.py`. Cuando identifica un incidente de
seguridad, publica `NotificacionIncidenteSeguridad` en el broker (lo consume
`ms-notificaciones`).

## Qué consume / qué produce (`tareas/consumidores.py`)

| | valor |
|---|---|
| tareas Celery | `audit.registrar_sesion_accion`, `audit.registrar_extraccion_perfil` |
| colas | `audit.sesion_accion.q`, `audit.extraccion_perfil.q` |
| exchange | `solventa-seguridad` (topic) |
| produce | `audit.incidente_seguridad` → tarea `notificaciones.notificar_incidente` |

Pendiente:
- Modelo de datos `HistorialRegistrosUsuario` + `HistorialConexion` en PostgreSQL.
- `clasificador_intrusiones.py`: lógica de detección real (ver TODO en el archivo).
- Publicación de `NotificacionIncidenteSeguridad` cuando se detecta un incidente.
- Medir y validar en la práctica el spike de latencia del camino asíncrono
  (publicar→broker→consumir→clasificar) contra el umbral de 200 ms de ASR1 —
  ver el punto de incertidumbre documentado en el diseño del experimento.
