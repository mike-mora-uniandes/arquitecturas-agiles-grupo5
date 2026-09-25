"""Configuración de MS Notificaciones leída desde variables de entorno."""
import os


class Config:
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672//")
    RABBITMQ_EXCHANGE = os.getenv("RABBITMQ_EXCHANGE", "solventa-seguridad")

    INCIDENTE_QUEUE = os.getenv("INCIDENTE_QUEUE", "notificaciones.incidente.q")
    INCIDENTE_ROUTING_KEY = os.getenv(
        "INCIDENTE_ROUTING_KEY", "audit.incidente_seguridad"
    )
    NOTIFICAR_INCIDENTE_TASK_NAME = os.getenv(
        "NOTIFICAR_INCIDENTE_TASK_NAME", "notificaciones.notificar_incidente"
    )

    # Umbral de reacción (ASR3 confidencialidad / ASR4 integridad): notificar
    # al analista en < 5 s desde la detección.
    ASR_NOTIFICACION_UMBRAL_MS = float(
        os.getenv("ASR_NOTIFICACION_UMBRAL_MS", "5000")
    )

    CELERY_CONCURRENCY = int(os.getenv("CELERY_CONCURRENCY", "1"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
