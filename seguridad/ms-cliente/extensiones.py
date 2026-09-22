"""Extensiones compartidas del microservicio (sin broker — ver config.py)."""
import requests

# Sesión reutilizable hacia MS Identidad / MS Riesgo (logica/orquestador.py).
sesion_http = requests.Session()
