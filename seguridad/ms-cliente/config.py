"""Configuración de MS Cliente leída desde variables de entorno."""
import os


class Config:
    # Sin broker: es el único servicio del experimento que no publica ni
    # consume del Event Bus (ver ../README.md, tabla de conectores).
    MS_IDENTIDAD_URL = os.getenv("MS_IDENTIDAD_URL", "http://ms-identidad:5000")
    MS_RIESGO_URL = os.getenv("MS_RIESGO_URL", "http://ms-riesgo:5000")

    # Mismo secreto que GeneradorIntegridad (ms-riesgo) — ver
    # logica/validador_integridad.py.
    INTEGRITY_SECRET = os.getenv("INTEGRITY_SECRET", "change-me")

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
