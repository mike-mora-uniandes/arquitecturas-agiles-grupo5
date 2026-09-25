"""Configuración de MS Identidad leída desde variables de entorno."""
import os


class Config:
    # GestiónRoles (roles y permisos) — PostgreSQL propio de este servicio.
    # Nombre de variable específico (no "DATABASE_URL" a secas): el .env se
    # comparte entre los 5 servicios, y ms-riesgo/ms-audit tienen su propia
    # base — un nombre genérico se pisaría entre ellos.
    DATABASE_URL = os.getenv(
        "IDENTIDAD_DATABASE_URL",
        "postgresql://solventa:solventa@ms-identidad-db:5432/identidad",
    )

    JWT_SECRET = os.getenv("JWT_SECRET", "change-me")

    # Publicación async del reporte de sesión/acción (consumido por MS Audit).
    # Nombres coordinados con ../ms-audit/config.py — deben coincidir.
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672//")
    RABBITMQ_EXCHANGE = os.getenv("RABBITMQ_EXCHANGE", "solventa-seguridad")
    SESION_ACCION_QUEUE = os.getenv("SESION_ACCION_QUEUE", "audit.sesion_accion.q")
    SESION_ACCION_ROUTING_KEY = os.getenv(
        "SESION_ACCION_ROUTING_KEY", "identidad.sesion_accion"
    )
    SESION_ACCION_TASK_NAME = os.getenv(
        "SESION_ACCION_TASK_NAME", "audit.registrar_sesion_accion"
    )

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
