"""Configuración de MS PerfilRiesgo leída desde variables de entorno."""
import os


class Config:
    # Infraestructura.
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672//")
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

    # Fuentes externas (simuladas con Wiremock). El microservicio consulta
    # {URL}/customers/{customer_id}; el escenario lo elige Wiremock por customer_id.
    OPEN_DATA_URL = os.getenv("OPEN_DATA_URL", "http://wiremock:8080/open-data")
    OPEN_FINANCE_URL = os.getenv(
        "OPEN_FINANCE_URL", "http://wiremock:8080/open-finance"
    )

    # Tácticas de disponibilidad.
    DETECTION_TIMEOUT_MS = int(os.getenv("DETECTION_TIMEOUT_MS", "700"))      # ASR1
    RETRY_MAX = int(os.getenv("RETRY_MAX", "3"))                            # ASR3
    RETRY_BACKOFF_BASE_MS = int(os.getenv("RETRY_BACKOFF_BASE_MS", "200"))  # ASR3
    RETRY_BUDGET_MS = int(os.getenv("RETRY_BUDGET_MS", "5000"))            # ASR3
    CACHE_TTL_S = int(os.getenv("CACHE_TTL_S", "86400"))                  # ASR2
    CACHE_ASR2_THRESHOLD_MS = int(os.getenv("CACHE_ASR2_THRESHOLD_MS", "100"))  # ASR2

    # Idempotencia: clave processed:{correlation_id}.
    PROCESSED_TTL_S = int(os.getenv("PROCESSED_TTL_S", "3600"))

    # Worker Celery.
    CELERY_CONCURRENCY = int(os.getenv("CELERY_CONCURRENCY", "4"))

    # Topología RabbitMQ (según DESIGN.md §2.2 — pendiente de confirmar con el equipo).
    RABBITMQ_EXCHANGE = os.getenv("RABBITMQ_EXCHANGE", "solventa")
    RABBITMQ_DLX = os.getenv("RABBITMQ_DLX", "solventa.dlx")
    REQUEST_QUEUE = os.getenv("REQUEST_QUEUE", "profile.request.q")
    REQUEST_ROUTING_KEY = os.getenv("REQUEST_ROUTING_KEY", "profile.request")
    RESULT_QUEUE = os.getenv("RESULT_QUEUE", "profile.result.q")
    RESULT_ROUTING_KEY = os.getenv("RESULT_ROUTING_KEY", "profile.result")
    # Nombre de la tarea Celery que consume MS Notificaciones (DESIGN.md §2.1).
    RESULT_TASK_NAME = os.getenv("RESULT_TASK_NAME", "notificaciones.deliver_result")

    # Contrato / cálculo.
    SCHEMA_VERSION = os.getenv("SCHEMA_VERSION", "1")
    MODEL_VERSION = os.getenv("MODEL_VERSION", "v1")

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
