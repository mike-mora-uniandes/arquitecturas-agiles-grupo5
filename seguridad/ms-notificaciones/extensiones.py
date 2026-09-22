"""Extensiones compartidas del microservicio: Celery y topología AMQP."""
from celery import Celery
from kombu import Exchange, Queue

from config import Config

_exchange = Exchange(Config.RABBITMQ_EXCHANGE, type="topic", durable=True)

_incidente_queue = Queue(
    Config.INCIDENTE_QUEUE,
    _exchange,
    routing_key=Config.INCIDENTE_ROUTING_KEY,
    durable=True,
)

celery_app = Celery("ms_notificaciones", broker=Config.RABBITMQ_URL)
celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    task_serializer="json",
    accept_content=["json"],
    task_default_exchange=Config.RABBITMQ_EXCHANGE,
    task_default_exchange_type="topic",
    task_queues=[_incidente_queue],
    task_routes={
        Config.NOTIFICAR_INCIDENTE_TASK_NAME: {
            "queue": Config.INCIDENTE_QUEUE,
            "routing_key": Config.INCIDENTE_ROUTING_KEY,
        },
    },
)
