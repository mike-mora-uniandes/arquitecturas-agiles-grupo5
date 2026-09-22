"""Configuración de MS Cliente leída desde variables de entorno."""
import os


class Config:
    MS_IDENTIDAD_URL = os.getenv("MS_IDENTIDAD_URL", "http://ms-identidad:5000")
    MS_RIESGO_URL = os.getenv("MS_RIESGO_URL", "http://ms-riesgo:5000")

    # Mismo secreto que GeneradorIntegridad (ms-riesgo) — ver
    # logica/validador_integridad.py.
    INTEGRITY_SECRET = os.getenv("INTEGRITY_SECRET", "change-me")

    # Productor puro (sin worker): solo publica IntegridadFallida al broker
    # cuando el hash del perfil no coincide (ASR2). La detección es inline y
    # autónoma aquí; ms-audit centraliza métrica + notificación (ver
    # ../ms-audit/README.md). Nombres coordinados con ms-audit — deben
    # coincidir.
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672//")
    RABBITMQ_EXCHANGE = os.getenv("RABBITMQ_EXCHANGE", "solventa-seguridad")
    INTEGRIDAD_QUEUE = os.getenv("INTEGRIDAD_QUEUE", "audit.integridad_fallida.q")
    INTEGRIDAD_ROUTING_KEY = os.getenv(
        "INTEGRIDAD_ROUTING_KEY", "cliente.integridad_fallida"
    )
    INTEGRIDAD_TASK_NAME = os.getenv(
        "INTEGRIDAD_TASK_NAME", "audit.registrar_integridad_fallida"
    )

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
