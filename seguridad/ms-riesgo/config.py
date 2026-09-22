"""Configuración de MS Riesgo leída desde variables de entorno."""
import os


class Config:
    # Base de datos PerfilRiesgo (datos sensibles del cliente) — el objetivo
    # del ataque de confidencialidad (ASR1).
    # Nombre de variable específico — ver la misma nota en
    # ../ms-identidad/config.py (el .env se comparte entre los 5 servicios).
    DATABASE_URL = os.getenv(
        "RIESGO_DATABASE_URL",
        "postgresql://solventa:solventa@ms-riesgo-db:5432/perfilriesgo",
    )

    # Firma del perfil antes de entregarlo (GeneradorIntegridad).
    INTEGRITY_SECRET = os.getenv("INTEGRITY_SECRET", "change-me")

    # Publicación async del reporte de extracción (consumido por MS Audit).
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672//")
    RABBITMQ_EXCHANGE = os.getenv("RABBITMQ_EXCHANGE", "solventa-seguridad")
    EXTRACCION_ROUTING_KEY = os.getenv(
        "EXTRACCION_ROUTING_KEY", "riesgo.extraccion_perfil"
    )

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
