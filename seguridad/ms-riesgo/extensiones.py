"""Extensiones compartidas del microservicio: Celery (cliente, solo publica)
y BD (PerfilRiesgo).
"""
import time

from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import scoped_session, sessionmaker

from config import Config


def esperar_bd(engine, intentos=15, espera_s=2):
    """Postgres puede tardar unos segundos en aceptar conexiones tras
    arrancar — depends_on solo espera a que el contenedor inicie, no a que
    el servidor esté listo (mismo patrón que
    ../ms-identidad/extensiones.py y seed/generar_seed.py).
    """
    for intento in range(1, intentos + 1):
        try:
            with engine.connect():
                return
        except OperationalError:
            if intento == intentos:
                raise
            time.sleep(espera_s)


# Productor puro: publica ReporteExtraccionPerfilRiesgoCliente, no consume —
# no corre worker (ver run.sh).
celery_app = Celery("ms_riesgo", broker=Config.RABBITMQ_URL)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    task_default_exchange=Config.RABBITMQ_EXCHANGE,
    task_default_exchange_type="topic",
)

# BD PerfilRiesgo.
engine = create_engine(Config.DATABASE_URL, pool_pre_ping=True)
Session = scoped_session(sessionmaker(bind=engine))
