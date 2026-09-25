"""Configuración de MS Riesgo leída desde variables de entorno."""
import os


class Config:
    # Base de datos PerfilRiesgo (datos sensibles del cliente) — el objetivo
    # del ataque de confidencialidad (ASR1).
    # Nombre de variable específico (no "DATABASE_URL" a secas): el .env se
    # comparte entre los 5 servicios, y ya estaba definido así en
    # ../.env.example desde el scaffolding original — este servicio no lo
    # leía todavía.
    DATABASE_URL = os.getenv(
        "RIESGO_DATABASE_URL",
        "postgresql://solventa:solventa@ms-riesgo-db:5432/perfilriesgo",
    )

    # Firma del perfil antes de entregarlo (GeneradorIntegridad).
    INTEGRITY_SECRET = os.getenv("INTEGRITY_SECRET", "change-me")

    # Publicación async del reporte de extracción (consumido por MS Audit).
    # Nombres coordinados con ../ms-audit/config.py — deben coincidir.
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672//")
    RABBITMQ_EXCHANGE = os.getenv("RABBITMQ_EXCHANGE", "solventa-seguridad")
    EXTRACCION_QUEUE = os.getenv("EXTRACCION_QUEUE", "audit.extraccion_perfil.q")
    EXTRACCION_ROUTING_KEY = os.getenv(
        "EXTRACCION_ROUTING_KEY", "riesgo.extraccion_perfil"
    )
    # Coincide con el nombre hardcodeado en ms-audit/tareas/consumidores.py —
    # si se convierte a Config.EXTRACCION_TASK_NAME allá también, deben
    # seguir coincidiendo.
    EXTRACCION_TASK_NAME = os.getenv(
        "EXTRACCION_TASK_NAME", "audit.registrar_extraccion_perfil"
    )

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
