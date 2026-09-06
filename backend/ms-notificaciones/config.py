"""Configuración de MS Notificaciones leída desde variables de entorno."""
import os


class Config:
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672//")
    RETRY_MAX = int(os.getenv("RETRY_MAX", "3"))   # reintentos antes de la DLQ
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Topología RabbitMQ (debe coincidir con ../ms-perfil-riesgo/config.py).
    RABBITMQ_EXCHANGE = os.getenv("RABBITMQ_EXCHANGE", "solventa")
    RABBITMQ_DLX = os.getenv("RABBITMQ_DLX", "solventa.dlx")
    RESULT_QUEUE = os.getenv("RESULT_QUEUE", "profile.result.q")
    RESULT_ROUTING_KEY = os.getenv("RESULT_ROUTING_KEY", "profile.result")
    # Nombre de la tarea Celery que expone este servicio (la publica MS PerfilRiesgo).
    RESULT_TASK_NAME = os.getenv("RESULT_TASK_NAME", "notificaciones.deliver_result")
