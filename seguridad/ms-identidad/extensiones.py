"""Extensiones compartidas del microservicio: Celery (cliente, solo publica)
y BD (GestiónRoles).
"""
import time

from celery import Celery
from kombu import Exchange, Queue
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import scoped_session, sessionmaker

from config import Config


def esperar_bd(engine, intentos=15, espera_s=2):
    """Postgres puede tardar unos segundos en aceptar conexiones tras
    arrancar — depends_on solo espera a que el contenedor inicie, no a que
    el servidor esté listo (mismo patrón de reintento que seed/generar_seed.py
    y que Celery/RabbitMQ en el resto del proyecto).
    """
    for intento in range(1, intentos + 1):
        try:
            with engine.connect():
                return
        except OperationalError:
            if intento == intentos:
                raise
            time.sleep(espera_s)

_exchange = Exchange(Config.RABBITMQ_EXCHANGE, type="topic", durable=True)

# Servicio productor puro: usa Celery como cliente (send_task) para publicar
# ReporteSesionAccion, pero no consume nada — por eso no corre un worker
# (ver run.sh). Declara la cola igual que ms-riesgos/ms-riesgos del
# experimento 1: el productor deja la topología lista aunque su consumer
# (ms-audit) no haya arrancado todavía.
_sesion_accion_queue = Queue(
    Config.SESION_ACCION_QUEUE,
    _exchange,
    routing_key=Config.SESION_ACCION_ROUTING_KEY,
    durable=True,
)

celery_app = Celery("ms_identidad", broker=Config.RABBITMQ_URL)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    task_default_exchange=Config.RABBITMQ_EXCHANGE,
    task_default_exchange_type="topic",
    task_queues=[_sesion_accion_queue],
    task_routes={
        Config.SESION_ACCION_TASK_NAME: {
            "queue": Config.SESION_ACCION_QUEUE,
            "routing_key": Config.SESION_ACCION_ROUTING_KEY,
        },
    },
)

# BD GestiónRoles.
engine = create_engine(Config.DATABASE_URL, pool_pre_ping=True)
Session = scoped_session(sessionmaker(bind=engine))
