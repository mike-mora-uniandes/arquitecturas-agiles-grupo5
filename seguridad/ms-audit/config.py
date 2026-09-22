"""Configuración de MS Audit leída desde variables de entorno."""
import os


class Config:
    # HistorialRegistrosUsuario + HistorialConexion — PostgreSQL propio.
    DATABASE_URL = os.getenv(
        "DATABASE_URL", "postgresql://solventa:solventa@ms-audit-db:5432/audit"
    )

    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672//")
    RABBITMQ_EXCHANGE = os.getenv("RABBITMQ_EXCHANGE", "solventa-seguridad")

    # Consume (de ms-identidad y ms-riesgo).
    SESION_ACCION_QUEUE = os.getenv("SESION_ACCION_QUEUE", "audit.sesion_accion.q")
    SESION_ACCION_ROUTING_KEY = os.getenv(
        "SESION_ACCION_ROUTING_KEY", "identidad.sesion_accion"
    )
    EXTRACCION_QUEUE = os.getenv("EXTRACCION_QUEUE", "audit.extraccion_perfil.q")
    EXTRACCION_ROUTING_KEY = os.getenv(
        "EXTRACCION_ROUTING_KEY", "riesgo.extraccion_perfil"
    )

    # Produce (lo consume ms-notificaciones).
    INCIDENTE_ROUTING_KEY = os.getenv(
        "INCIDENTE_ROUTING_KEY", "audit.incidente_seguridad"
    )
    NOTIFICAR_INCIDENTE_TASK_NAME = os.getenv(
        "NOTIFICAR_INCIDENTE_TASK_NAME", "notificaciones.notificar_incidente"
    )

    CELERY_CONCURRENCY = int(os.getenv("CELERY_CONCURRENCY", "2"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
