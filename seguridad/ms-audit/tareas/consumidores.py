"""Tareas Celery que consumen los eventos de ms-identidad y ms-riesgo, y
publican el incidente cuando el clasificador detecta una intrusión.
"""
import logging

from config import Config
from extensiones import celery_app

log = logging.getLogger(__name__)


@celery_app.task(bind=True, name=Config.SESION_ACCION_TASK_NAME)
def registrar_sesion_accion(self, evento):
    log.info("ReporteSesionAccion recibido: %s", evento)
    # TODO: persistir en HistorialConexion + pasar por clasificador_intrusiones.


@celery_app.task(bind=True, name="audit.registrar_extraccion_perfil")
def registrar_extraccion_perfil(self, evento):
    log.info("ReporteExtraccionPerfilRiesgoCliente recibido: %s", evento)
    # TODO: persistir en HistorialRegistrosUsuario + pasar por clasificador_intrusiones.
