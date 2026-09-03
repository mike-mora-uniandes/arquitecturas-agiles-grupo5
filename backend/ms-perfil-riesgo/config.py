"""Configuración de MS PerfilRiesgo leída desde variables de entorno.

Los parámetros de las tácticas de disponibilidad se declaran aquí como
contrato; su uso se implementará junto con la lógica de ASR1/ASR2/ASR3.
"""
import os


class Config:
    # Infraestructura.
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672//")
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

    # Fuentes externas (simuladas con Wiremock).
    OPEN_DATA_URL = os.getenv("OPEN_DATA_URL", "http://wiremock:8080/open-data")
    OPEN_FINANCE_URL = os.getenv(
        "OPEN_FINANCE_URL", "http://wiremock:8080/open-finance"
    )

    # Tácticas de disponibilidad (aún sin implementar).
    DETECTION_TIMEOUT_MS = int(os.getenv("DETECTION_TIMEOUT_MS", "700"))      # ASR1
    RETRY_MAX = int(os.getenv("RETRY_MAX", "3"))                            # ASR3
    RETRY_BACKOFF_BASE_MS = int(os.getenv("RETRY_BACKOFF_BASE_MS", "200"))  # ASR3
    RETRY_BUDGET_MS = int(os.getenv("RETRY_BUDGET_MS", "5000"))            # ASR3
    CACHE_TTL_S = int(os.getenv("CACHE_TTL_S", "86400"))                  # ASR2

    # Idempotencia: clave processed:{correlation_id}.
    PROCESSED_TTL_S = int(os.getenv("PROCESSED_TTL_S", "3600"))

    # Worker Celery.
    CELERY_CONCURRENCY = int(os.getenv("CELERY_CONCURRENCY", "4"))

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
