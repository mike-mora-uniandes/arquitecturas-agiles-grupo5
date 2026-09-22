"""Tarea Celery que consume NotificacionIncidenteSeguridad (la publica
MS Audit) y avisa al analista de riesgo — implementa ASR3/ASR4 (reacción).
"""
import logging

from config import Config
from extensiones import celery_app

log = logging.getLogger(__name__)


@celery_app.task(bind=True, name=Config.NOTIFICAR_INCIDENTE_TASK_NAME)
def notificar_incidente(self, incidente):
    log.info("NotificacionIncidenteSeguridad recibido: %s", incidente)
    # TODO: notificar al analista de riesgo (ASR3 confidencialidad / ASR4
    # integridad) en menos de 5s desde la detección.
