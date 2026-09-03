"""Declaración del dead-letter exchange y sus colas (DESIGN.md §2.2).

Celery declara `profile.request.q` a partir de `task_queues`, pero no el DLX ni
las colas muertas. Este módulo lo hace al arrancar el worker.
"""
import logging

from celery.signals import worker_ready
from kombu import Connection, Exchange, Queue

from config import Config

log = logging.getLogger(__name__)


def _declarar():
    dlx = Exchange(Config.RABBITMQ_DLX, type="topic", durable=True)
    with Connection(Config.RABBITMQ_URL) as conn:
        canal = conn.channel()
        dlx(canal).declare()
        for rk in (Config.REQUEST_ROUTING_KEY, Config.RESULT_ROUTING_KEY):
            Queue(f"{rk}.dead.q", dlx, routing_key=f"{rk}.dead", durable=True)(
                canal
            ).declare()


@worker_ready.connect
def declarar_dead_letter(**_):
    try:
        _declarar()
        log.info("Dead-letter exchange y colas declarados.")
    except Exception as exc:  # no bloquear el arranque del worker
        log.warning("No se pudo declarar el dead-letter: %s", exc)
