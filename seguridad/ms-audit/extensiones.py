"""Extensiones compartidas del microservicio: Celery (consume 3 eventos,
produce 1) y BD (HistorialConexion, HistorialRegistrosUsuario, Incidente).
"""
import time

from celery import Celery
from celery.signals import worker_init, worker_process_init
from kombu import Exchange, Queue
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import scoped_session, sessionmaker

from config import Config


def esperar_bd(engine, intentos=15, espera_s=2):
    """Postgres puede tardar unos segundos en aceptar conexiones tras
    arrancar — depends_on solo espera a que el contenedor inicie, no a que el
    servidor esté listo (mismo patrón que ../ms-identidad/extensiones.py y
    seed/generar_seed.py).
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
_integridad_queue = Queue(
    Config.INTEGRIDAD_QUEUE,
    _exchange,
    routing_key=Config.INTEGRIDAD_ROUTING_KEY,
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
    task_queues=[_sesion_accion_queue, _extraccion_queue, _integridad_queue],
    task_routes={
        Config.SESION_ACCION_TASK_NAME: {
            "queue": Config.SESION_ACCION_QUEUE,
            "routing_key": Config.SESION_ACCION_ROUTING_KEY,
        },
        Config.EXTRACCION_TASK_NAME: {
            "queue": Config.EXTRACCION_QUEUE,
            "routing_key": Config.EXTRACCION_ROUTING_KEY,
        },
        Config.INTEGRIDAD_TASK_NAME: {
            "queue": Config.INTEGRIDAD_QUEUE,
            "routing_key": Config.INTEGRIDAD_ROUTING_KEY,
        },
    },
)

# BD de auditoría (HistorialConexion, HistorialRegistrosUsuario, Incidente).
engine = create_engine(Config.DATABASE_URL, pool_pre_ping=True)
Session = scoped_session(sessionmaker(bind=engine))


def inicializar_bd():
    """Espera a Postgres y crea las tablas si no existen. Idempotente."""
    from logica.modelos import Base  # import diferido: evita ciclo con modelos

    esperar_bd(engine)
    Base.metadata.create_all(engine)


@worker_init.connect(weak=False)
def _preparar_bd_worker(**_kwargs):
    """A diferencia de ms-identidad/ms-riesgo (productores puros), el worker de
    ms-audit escribe en la BD, así que las tablas deben existir antes de
    procesar el primer evento. worker_init corre una vez en el proceso padre
    del worker, antes de forkear los hijos del pool prefork.
    """
    inicializar_bd()


@worker_process_init.connect(weak=False)
def _renovar_conexiones_bd(**_kwargs):
    """Cada hijo del pool prefork debe descartar las conexiones heredadas del
    proceso padre: las conexiones de psycopg2/libpq NO se pueden compartir
    entre procesos tras un fork (dos hijos usando la misma conexión corrompen
    el resultado — 'PGRES_TUPLES_OK and no message' / ResourceClosedError).
    `engine.dispose()` vacía el pool heredado; cada hijo abre conexiones
    nuevas de forma perezosa. (El engine se crea en el padre, antes del fork,
    por eso hay que renovarlo aquí y no en worker_init.)
    """
    engine.dispose()
