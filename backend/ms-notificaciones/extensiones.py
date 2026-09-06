"""Extensiones compartidas del microservicio: Celery y topología AMQP."""
from celery import Celery
from kombu import Exchange, Queue

from config import Config

import telemetria  # noqa: F401  (registra el filtro de logs de OTel)

_exchange = Exchange(Config.RABBITMQ_EXCHANGE, type="topic", durable=True)

# Cola de resultados: clásica durable + dead-letter (el DLX lo declara
# MS PerfilRiesgo al arrancar — ver ../ms-perfil-riesgo/topologia.py).
_result_queue = Queue(
    Config.RESULT_QUEUE,
    _exchange,
    routing_key=Config.RESULT_ROUTING_KEY,
    durable=True,
    queue_arguments={
        "x-dead-letter-exchange": Config.RABBITMQ_DLX,
        "x-dead-letter-routing-key": f"{Config.RESULT_ROUTING_KEY}.dead",
    },
)

celery_app = Celery("ms_notificaciones", broker=Config.RABBITMQ_URL)
celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    worker_cancel_long_running_tasks_on_connection_loss=True,
    task_serializer="json",
    accept_content=["json"],
    task_default_exchange=Config.RABBITMQ_EXCHANGE,
    task_default_exchange_type="topic",
    task_queues=[_result_queue],
    task_routes={
        Config.RESULT_TASK_NAME: {
            "queue": Config.RESULT_QUEUE,
            "routing_key": Config.RESULT_ROUTING_KEY,
        },
    },
)
