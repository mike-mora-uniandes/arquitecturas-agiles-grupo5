"""Tarea Celery que consume NotificacionIncidenteSeguridad (la publica
MS Audit) y avisa al analista de riesgo — implementa ASR3/ASR4 (reacción).

La notificación real al analista se materializa como un log estructurado
(evidencia end-to-end, igual criterio que el experimento 1). Lo que sí se
mide con rigor es `tiempo_notificacion_ms`: el tiempo desde que ms-audit
detectó el incidente (`detectado_en` en el evento) hasta que llega aquí.
"""
import logging
from datetime import datetime, timezone

import telemetria
from config import Config
from extensiones import celery_app

log = logging.getLogger(__name__)

# Tipo de incidente → ASR de reacción, solo para etiquetar la métrica.
_ASR_POR_TIPO = {"confidencialidad": "ASR3", "integridad": "ASR4"}


def _parse_ts(valor: str) -> datetime:
    dt = datetime.fromisoformat(valor)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


@celery_app.task(bind=True, name=Config.NOTIFICAR_INCIDENTE_TASK_NAME)
def notificar_incidente(self, incidente):
    """`incidente` = dict publicado por ms-audit (tareas/publicador.py)."""
    log.info("NotificacionIncidenteSeguridad recibido: %s", incidente)

    tipo = incidente.get("tipo", "desconocido")
    asr = _ASR_POR_TIPO.get(tipo, "ASR?")

    detectado_en = _parse_ts(incidente["detectado_en"])
    ahora = datetime.now(timezone.utc)
    notificacion_ms = (ahora - detectado_en).total_seconds() * 1000.0
    dentro = notificacion_ms <= Config.ASR_NOTIFICACION_UMBRAL_MS

    telemetria.notificacion_ms.record(notificacion_ms, {"tipo": tipo})
    telemetria.asr_notificacion_within_total.add(
        1, {"tipo": tipo, "pass": str(dentro).lower()}
    )

    # "Notificación" al analista de riesgo: log estructurado como evidencia.
    log.warning(
        "NOTIFICAR ANALISTA [%s/%s] incidente=%s customer_id=%s "
        "notificacion_ms=%.1f dentro_umbral=%s :: %s",
        tipo, asr, incidente.get("incidente_id"), incidente.get("customer_id"),
        notificacion_ms, dentro, incidente.get("detalle"),
    )
