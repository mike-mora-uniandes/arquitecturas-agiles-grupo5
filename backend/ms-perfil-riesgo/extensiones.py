"""Extensiones compartidas del microservicio: Celery, Redis y topología AMQP."""
import redis
from celery import Celery
from kombu import Exchange, Queue

from config import Config

_exchange = Exchange(Config.RABBITMQ_EXCHANGE, type="topic", durable=True)

# Cola de solicitudes: clásica durable + dead-letter (DESIGN.md §2.2).
# Se usa clásica (no quorum) porque Celery 5.4 aplica QoS global al canal y las
# colas quorum solo aceptan QoS por consumidor (NOT_IMPLEMENTED / global qos).
# Con Celery >= 5.5 + worker_detect_quorum_queues se podría migrar a quorum.
_request_queue = Queue(
    Config.REQUEST_QUEUE,
    _exchange,
    routing_key=Config.REQUEST_ROUTING_KEY,
    durable=True,
    queue_arguments={
        "x-dead-letter-exchange": Config.RABBITMQ_DLX,
        "x-dead-letter-routing-key": f"{Config.REQUEST_ROUTING_KEY}.dead",
    },
)

celery_app = Celery("ms_perfil_riesgo", broker=Config.RABBITMQ_URL)
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
    task_queues=[_request_queue],
    task_routes={
        "perfil.evaluate_profile": {
            "queue": Config.REQUEST_QUEUE,
            "routing_key": Config.REQUEST_ROUTING_KEY,
        },
    },
)

# Cliente Redis (caché de datos externos / ASR2 e idempotencia).
# La conexión es perezosa: no se abre hasta el primer comando.
redis_client = redis.Redis.from_url(Config.REDIS_URL, decode_responses=True)

# Registra el handler que declara el dead-letter exchange y sus colas al arrancar.
from topologia import declarar_dead_letter  # noqa: E402,F401
