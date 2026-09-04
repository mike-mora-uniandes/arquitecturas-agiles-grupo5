"""Dispara el flujo end-to-end de MS PerfilRiesgo para poblar el experimento
de disponibilidad (ASR1/ASR2/ASR3) y ver los paneles de Grafana con datos
reales.

`ms-riesgos` (el productor real) y el endpoint `/evaluations` que usaria
Locust todavia son solo andamiaje (backend/README.md, seccion Pendiente), asi
que este script publica la tarea Celery `perfil.evaluate_profile`
directamente en RabbitMQ -- el mismo contrato que exige
`mensajes.parse_request` (correlation_id, customer_id) -- sin tocar
ms-perfil-riesgo.

Los customer_id usados estan fijados por los mappings de Wiremock
(../wiremock/README.md) y el seed de Redis (../redis/seed/profiles.redis):

    C001  OK ambas fuentes (linea base)
    C002  timeout ambas fuentes, se recupera al 2do intento -> ASR1 + ASR3 (retry exitoso)
    C003  503 persistente, CON respaldo en Redis            -> ASR1 + ASR3 (agotado) + ASR2 (hit)
    C004  503 persistente, CON respaldo en Redis             -> igual que C003
    C005  payload anomalo, no reintentable                   -> ASR2 (hit) directo
    C006  503 persistente, SIN respaldo en Redis              -> DEGRADED_NO_FALLBACK (no controlado)

Requisitos:
    pip install celery
    docker compose --profile experimento up -d --build   # RabbitMQ queda expuesto en localhost:5672

Uso:
    python disparar_experimento.py --rondas 5 --pausa 0.3
"""
import argparse
import os
import time
import uuid

from celery import Celery
from kombu import Exchange, Queue

CUSTOMERS = {
    "C001": "OK ambas fuentes (linea base)",
    "C002": "timeout ambas fuentes, se recupera al 2do intento (ASR1 + ASR3 retry exitoso)",
    "C003": "503 persistente, con respaldo en Redis (ASR3 agotado + ASR2 hit)",
    "C004": "503 persistente, con respaldo en Redis (ASR3 agotado + ASR2 hit)",
    "C005": "payload anomalo, no reintentable (ASR2 hit directo)",
    "C006": "503 persistente, SIN respaldo en Redis (fallo no controlado)",
}

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672//")
RABBITMQ_EXCHANGE = os.getenv("RABBITMQ_EXCHANGE", "solventa")
RABBITMQ_DLX = os.getenv("RABBITMQ_DLX", "solventa.dlx")
REQUEST_QUEUE = os.getenv("REQUEST_QUEUE", "profile.request.q")
REQUEST_ROUTING_KEY = os.getenv("REQUEST_ROUTING_KEY", "profile.request")


def _app() -> Celery:
    """Cliente Celery liviano: solo publica (no consume). La cola ya la
    declaro ms-perfil-riesgo (extensiones.py) con dead-letter-exchange; hay
    que declararla aqui con los MISMOS argumentos o RabbitMQ rechaza la
    declaracion por PRECONDITION_FAILED (406) al no coincidir.
    """
    exchange = Exchange(RABBITMQ_EXCHANGE, type="topic", durable=True)
    request_queue = Queue(
        REQUEST_QUEUE,
        exchange,
        routing_key=REQUEST_ROUTING_KEY,
        durable=True,
        queue_arguments={
            "x-dead-letter-exchange": RABBITMQ_DLX,
            "x-dead-letter-routing-key": f"{REQUEST_ROUTING_KEY}.dead",
        },
    )
    app = Celery("disparador_experimento", broker=RABBITMQ_URL)
    app.conf.task_default_exchange = RABBITMQ_EXCHANGE
    app.conf.task_default_exchange_type = "topic"
    app.conf.task_queues = [request_queue]
    app.conf.task_routes = {
        "perfil.evaluate_profile": {"queue": REQUEST_QUEUE, "routing_key": REQUEST_ROUTING_KEY},
    }
    return app


def disparar(app: Celery, customer_id: str) -> str:
    correlation_id = str(uuid.uuid4())
    body = {
        "correlation_id": correlation_id,
        "customer_id": customer_id,
        "requested_by": "disparar_experimento",
    }
    app.send_task(
        "perfil.evaluate_profile",
        args=[body],
        queue=REQUEST_QUEUE,
        routing_key=REQUEST_ROUTING_KEY,
    )
    return correlation_id


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rondas", type=int, default=3, help="veces que se recorre la matriz completa de customer_id (default: 3)")
    parser.add_argument("--pausa", type=float, default=0.5, help="segundos entre solicitudes (default: 0.5)")
    args = parser.parse_args()

    app = _app()
    total = 0
    for ronda in range(1, args.rondas + 1):
        for customer_id, descripcion in CUSTOMERS.items():
            cid = disparar(app, customer_id)
            total += 1
            print(f"[ronda {ronda}] {customer_id} ({descripcion}) -> correlation_id={cid}")
            time.sleep(args.pausa)

    print(f"\n{total} solicitudes publicadas en '{REQUEST_QUEUE}'. Revisa Grafana en http://localhost:3000")


if __name__ == "__main__":
    main()
