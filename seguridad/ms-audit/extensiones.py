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
    """Espera a Postgres, crea las tablas y siembra el historial normal inicial
    si está vacío. Idempotente.
    """
    from logica.modelos import Base  # import diferido: evita ciclo con modelos

    esperar_bd(engine)
    Base.metadata.create_all(engine)
    _autosembrar_historial_normal()


def _autosembrar_historial_normal():
    """Da una línea base de comportamiento desde la primera request: inserta
    unas conexiones legítimas por cliente (país/device habitual) SOLO si el
    historial está vacío. Respaldo del seed, que también llena esta tabla; el
    guard por "vacío" evita duplicar cuando ambos corren. ms-audit es dueño de
    su esquema, así que sembrar aquí no lo acopla a la seed.
    """
    from datetime import datetime, timezone

    from logica.modelos import HistorialConexion

    session = Session()
    try:
        if session.query(HistorialConexion.id).first() is not None:
            return  # ya hay historial (lo llenó el seed o una corrida previa)

        ahora = datetime.now(timezone.utc)
        filas = []
        for indice in range(1, Config.AUTOSEED_N_CLIENTES + 1):
            cid = f"CLI-{indice:04d}"
            for _ in range(Config.AUTOSEED_CONEXIONES):
                filas.append(
                    HistorialConexion(
                        request_id=None,
                        customer_id_token=cid,
                        customer_id_solicitado=cid,
                        validado=True,
                        ip="10.0.0.5",
                        device=Config.AUTOSEED_DEVICE,
                        pais=Config.AUTOSEED_PAIS,
                        reportado_en=ahora,
                        anomala=False,
                    )
                )
        session.add_all(filas)
        session.commit()
    finally:
        Session.remove()


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
