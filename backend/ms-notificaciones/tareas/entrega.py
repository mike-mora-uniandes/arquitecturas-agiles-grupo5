"""Tarea Celery que consume ProfileEvaluationResult (la publica MS PerfilRiesgo).

Por ahora solo se loguea — el mecanismo real de notificación al analista de
riesgo (webhook, endpoint de consulta, etc.) todavía lo debe confirmar el
equipo. El log sirve como métrica de validación end-to-end del Event Bus.
"""
import logging

from config import Config
from extensiones import celery_app

log = logging.getLogger(__name__)


@celery_app.task(bind=True, name=Config.RESULT_TASK_NAME)
def deliver_result(self, resultado):
    log.info("ProfileEvaluationResult recibido: %s", resultado)
    return "logged"
