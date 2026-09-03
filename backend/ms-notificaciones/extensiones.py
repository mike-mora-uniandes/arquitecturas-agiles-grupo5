"""Extensiones compartidas del microservicio (sin lógica de negocio)."""
from celery import Celery

from config import Config

# Transporte configurado; el consumidor del resultado vivirá en 'tareas'.
celery_app = Celery("ms_notificaciones", broker=Config.RABBITMQ_URL)
