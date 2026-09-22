"""Configuración de MS Identidad leída desde variables de entorno."""
import os


class Config:
    # GestiónRoles (roles y permisos) — PostgreSQL propio de este servicio.
    DATABASE_URL = os.getenv(
        "DATABASE_URL", "postgresql://solventa:solventa@ms-identidad-db:5432/identidad"
    )

    JWT_SECRET = os.getenv("JWT_SECRET", "change-me")

    # Publicación async del reporte de sesión/acción (consumido por MS Audit).
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672//")
    RABBITMQ_EXCHANGE = os.getenv("RABBITMQ_EXCHANGE", "solventa-seguridad")
    SESION_ACCION_ROUTING_KEY = os.getenv(
        "SESION_ACCION_ROUTING_KEY", "identidad.sesion_accion"
    )

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
