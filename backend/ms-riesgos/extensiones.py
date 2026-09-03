"""Extensiones compartidas del microservicio (sin lógica de negocio)."""
from celery import Celery

from config import Config

# Transporte configurado; los publicadores/consumidores vivirán en 'tareas'.
celery_app = Celery("ms_riesgos", broker=Config.RABBITMQ_URL)
