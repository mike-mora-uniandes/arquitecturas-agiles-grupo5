"""Configuración de MS PerfilRiesgo leída desde variables de entorno.

Los parámetros de las tácticas de disponibilidad se declaran aquí como
contrato; su uso se implementará junto con la lógica de ASR1/ASR2/ASR3.
"""
import os


class Config:
    # Persistencia local (modelo de escritura del microservicio).
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:////backend/perfil-riesgo.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Infraestructura.
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672//")
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

    # Fuentes externas (simuladas con Wiremock).
    OPEN_DATA_URL = os.getenv("OPEN_DATA_URL", "http://wiremock:8080/open-data")
    OPEN_FINANCE_URL = os.getenv(
        "OPEN_FINANCE_URL", "http://wiremock:8080/open-finance"
    )

    # Tácticas de disponibilidad (aún sin implementar).
    DETECCION_TIMEOUT_MS = int(os.getenv("DETECCION_TIMEOUT_MS", "700"))      # ASR1
    RETRY_MAX = int(os.getenv("RETRY_MAX", "3"))                             # ASR3
    RETRY_BACKOFF_BASE_MS = int(os.getenv("RETRY_BACKOFF_BASE_MS", "200"))   # ASR3
    RETRY_PRESUPUESTO_MS = int(os.getenv("RETRY_PRESUPUESTO_MS", "5000"))    # ASR3
    CACHE_TTL_S = int(os.getenv("CACHE_TTL_S", "86400"))                     # ASR2

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
