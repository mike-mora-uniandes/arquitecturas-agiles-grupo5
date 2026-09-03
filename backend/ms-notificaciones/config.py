"""Configuración de MS Notificaciones leída desde variables de entorno."""
import os


class Config:
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672//")
    RETRY_MAX = int(os.getenv("RETRY_MAX", "3"))   # reintentos antes de la DLQ
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
