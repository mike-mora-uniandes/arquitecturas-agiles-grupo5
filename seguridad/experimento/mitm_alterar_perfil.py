"""Escenario 2 — Integridad (ASR2).

Addon de mitmproxy: intercepta la respuesta síncrona de ms-riesgo hacia
ms-cliente (comunicación HTTP directa, sin broker de por medio) y altera el
payload del perfil de riesgo en tránsito, dejando el hash de integridad
original sin actualizar — así ValidadorIntegridad (ms-cliente) debe
detectar la manipulación.

Uso:
    mitmdump -s mitm_alterar_perfil.py -p 8081 \
        --mode reverse:http://ms-riesgo:5000

Y apuntar MS_RIESGO_URL de ms-cliente a este proxy (puerto 8081) en vez de
al servicio real, solo durante la corrida del escenario de integridad.
"""
import json
import logging

from mitmproxy import http


log = logging.getLogger(__name__)


def response(flow: http.HTTPFlow) -> None:
    if "/perfiles" not in flow.request.path:
        return
    try:
        payload = json.loads(flow.response.content)
    except (ValueError, TypeError):
        return
    # Altera el `puntaje` del perfil (el campo real que entrega ms-riesgo)
    # SIN recalcular el hash_integridad, dejando evidencia de manipulación en
    # tránsito. ValidadorIntegridad (ms-cliente) recalcula el hash sobre el
    # payload alterado, no coincide, y detecta la intrusión (ASR2).
    if "puntaje" not in payload:
        return
    puntaje_original = payload["puntaje"]
    payload["puntaje"] = 999  # valor imposible (escala 0-100): evidencia clara
    flow.response.content = json.dumps(payload).encode("utf-8")

    customer_id = payload.get("customer_id", "desconocido")
    log.warning(
        "MITM altero perfil de customer_id=%s puntaje_original=%s puntaje_nuevo=%s",
        customer_id,
        puntaje_original,
        payload["puntaje"],
    )
