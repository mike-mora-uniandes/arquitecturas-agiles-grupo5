"""Extensiones compartidas del microservicio: Celery (cliente, solo publica) y BD."""
from celery import Celery

from config import Config

# Servicio productor puro: usa Celery como cliente (send_task) para publicar
# ReporteSesionAccion, pero no consume nada — por eso no corre un worker
# (ver run.sh) ni declara colas propias aquí.
celery_app = Celery("ms_identidad", broker=Config.RABBITMQ_URL)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    task_default_exchange=Config.RABBITMQ_EXCHANGE,
    task_default_exchange_type="topic",
)

# TODO: SQLAlchemy engine/session contra Config.DATABASE_URL (GestiónRoles)
# cuando se implemente ValidarUsuario.
