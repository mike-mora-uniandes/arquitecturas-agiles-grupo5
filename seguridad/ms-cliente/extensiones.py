"""Extensiones compartidas del microservicio: sesión HTTP (síncrona hacia
MS Identidad / MS Riesgo) y un productor Celery para publicar IntegridadFallida.

MS Cliente sigue sin consumir del broker (no corre worker): solo lo usa como
productor puro para reportar la manipulación de integridad que detecta inline,
igual patrón que ../ms-riesgo/extensiones.py y ../ms-identidad/extensiones.py.
"""
import requests
from celery import Celery
from kombu import Exchange, Queue

from config import Config

# Sesión reutilizable hacia MS Identidad / MS Riesgo (logica/orquestador.py).
sesion_http = requests.Session()

_exchange = Exchange(Config.RABBITMQ_EXCHANGE, type="topic", durable=True)

# Declara la cola aunque su consumidor (ms-audit) no haya arrancado todavía:
# sin esto, un mensaje publicado antes de que ms-audit vincule la cola se
# perdería (exchange topic sin cola vinculada).
_integridad_queue = Queue(
    Config.INTEGRIDAD_QUEUE,
    _exchange,
    routing_key=Config.INTEGRIDAD_ROUTING_KEY,
    durable=True,
)

celery_app = Celery("ms_cliente", broker=Config.RABBITMQ_URL)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    broker_connection_retry_on_startup=True,
    task_default_exchange=Config.RABBITMQ_EXCHANGE,
    task_default_exchange_type="topic",
    task_queues=[_integridad_queue],
    task_routes={
        Config.INTEGRIDAD_TASK_NAME: {
            "queue": Config.INTEGRIDAD_QUEUE,
            "routing_key": Config.INTEGRIDAD_ROUTING_KEY,
        },
    },
)
