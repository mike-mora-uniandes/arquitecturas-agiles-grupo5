# ms-notificaciones

Andamiaje: el servicio construye y arranca, sin lógica de negocio todavía.
API + worker Celery en el mismo contenedor (`run.sh`, `wait -n`), igual
patrón que el resto del experimento.

**Propósito final:** informar a los actores responsables (analista de riesgo)
los incidentes de seguridad identificados por `ms-audit` — cierra el ciclo de
reacción de ASR3 (confidencialidad) y ASR4 (integridad).

**Comportamiento esperado:** consume del Event Bus `NotificacionIncidenteSeguridad`
(`tareas/entrega.py`) y la comunica al analista de riesgo correspondiente, en
menos de 5 segundos desde la detección.

Pendiente:
- Mecanismo real de notificación al analista (queda por definir con el equipo,
  igual que en el experimento 1 — de momento loguear es suficiente evidencia
  end-to-end).
