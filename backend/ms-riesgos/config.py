"""Configuración de MS Riesgos leída desde variables de entorno."""
import os


class Config:
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672//")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
