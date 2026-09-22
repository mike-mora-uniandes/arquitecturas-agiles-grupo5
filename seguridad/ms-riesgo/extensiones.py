"""Extensiones compartidas del microservicio: Celery (cliente, solo publica) y BD."""
from celery import Celery

from config import Config

# Productor puro: publica ReporteExtraccionPerfilRiesgoCliente, no consume —
# no corre worker (ver run.sh).
celery_app = Celery("ms_riesgo", broker=Config.RABBITMQ_URL)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    task_default_exchange=Config.RABBITMQ_EXCHANGE,
    task_default_exchange_type="topic",
)

# TODO: SQLAlchemy engine/session contra Config.DATABASE_URL (PerfilRiesgo).
