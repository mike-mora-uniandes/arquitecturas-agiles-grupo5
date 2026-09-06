"""Extensiones compartidas del microservicio: Celery y topología AMQP."""
from celery import Celery
from kombu import Exchange, Queue

from config import Config

_exchange = Exchange(Config.RABBITMQ_EXCHANGE, type="topic", durable=True)
_request_queue = Queue(
    Config.REQUEST_QUEUE,
    _exchange,
    routing_key=Config.REQUEST_ROUTING_KEY,
    durable=True,
)

celery_app = Celery("ms_riesgos", broker=Config.RABBITMQ_URL)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    task_default_exchange=Config.RABBITMQ_EXCHANGE,
    task_default_exchange_type="topic",
    task_queues=[_request_queue],
    task_routes={
        "perfil.evaluate_profile": {
            "queue": Config.REQUEST_QUEUE,
            "routing_key": Config.REQUEST_ROUTING_KEY,
        },
    },
)
