"""Escenario 1 — Confidencialidad (ASR1).

Simula al atacante: forja/manipula un token de sesión (PyJWT) para pedirle a
ms-cliente el perfil de riesgo de una víctima sin pasar por el flujo normal
de ms-identidad, incluyendo datos dummy del atacante (IP/device/país
simulados — no GeoIP real, ver decisión documentada en el diseño del
experimento).
"""
import os

import jwt
import requests

MS_CLIENTE_URL = os.getenv("MS_CLIENTE_URL", "http://localhost:5000")
# TODO: reemplazar por el secreto real de ms-identidad una vez implementado
# (o dejar deliberadamente uno robado/filtrado, según el mecanismo final que
# defina el equipo para materializar el bypass).
JWT_SECRET = os.getenv("JWT_SECRET", "change-me")

ATACANTE = {
    "ip": "1.2.3.4",  # dummy — simula origen desde un país sancionado
    "device": "unknown-device",
    "pais": "IR",
}


def forjar_token(customer_id_victima: str) -> str:
    payload = {"sub": "atacante", "customer_id": customer_id_victima}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def ejecutar_ataque(customer_id_victima: str):
    token = forjar_token(customer_id_victima)
    # TODO: llamar a MS_CLIENTE_URL con el token forjado y los datos dummy
    # del atacante, y medir el tiempo hasta que ms-audit/ms-notificaciones
    # detecte y notifique el incidente (criterio de éxito de ASR1/ASR3).
    raise NotImplementedError


if __name__ == "__main__":
    ejecutar_ataque(customer_id_victima="CLI-0001")
