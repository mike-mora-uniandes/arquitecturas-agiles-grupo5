"""Configuración de MS Riesgos leída desde variables de entorno."""
import os


class Config:
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672//")

    RABBITMQ_EXCHANGE = os.getenv("RABBITMQ_EXCHANGE", "solventa")
    REQUEST_QUEUE = os.getenv("REQUEST_QUEUE", "profile.request.queue")
    REQUEST_ROUTING_KEY = os.getenv("REQUEST_ROUTING_KEY", "profile.request")
    RESULT_QUEUE = os.getenv("RESULT_QUEUE", "profile.result.queue")
    RESULT_ROUTING_KEY = os.getenv("RESULT_ROUTING_KEY", "profile.result")

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
