"""Extensiones compartidas del microservicio: Celery (consume 2 eventos,
produce 1) y BD.
"""
from celery import Celery
from kombu import Exchange, Queue

from config import Config

_exchange = Exchange(Config.RABBITMQ_EXCHANGE, type="topic", durable=True)

_sesion_accion_queue = Queue(
    Config.SESION_ACCION_QUEUE,
    _exchange,
    routing_key=Config.SESION_ACCION_ROUTING_KEY,
    durable=True,
)
_extraccion_queue = Queue(
    Config.EXTRACCION_QUEUE,
    _exchange,
    routing_key=Config.EXTRACCION_ROUTING_KEY,
    durable=True,
)

celery_app = Celery("ms_audit", broker=Config.RABBITMQ_URL)
celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    task_serializer="json",
    accept_content=["json"],
    task_default_exchange=Config.RABBITMQ_EXCHANGE,
    task_default_exchange_type="topic",
    task_queues=[_sesion_accion_queue, _extraccion_queue],
    task_routes={
        Config.SESION_ACCION_TASK_NAME: {
            "queue": Config.SESION_ACCION_QUEUE,
            "routing_key": Config.SESION_ACCION_ROUTING_KEY,
        },
        "audit.registrar_extraccion_perfil": {
            "queue": Config.EXTRACCION_QUEUE,
            "routing_key": Config.EXTRACCION_ROUTING_KEY,
        },
    },
)

# TODO: SQLAlchemy engine/session contra Config.DATABASE_URL
# (HistorialRegistrosUsuario, HistorialConexion).
