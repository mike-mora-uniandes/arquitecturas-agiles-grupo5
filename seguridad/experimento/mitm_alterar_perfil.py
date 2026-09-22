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
    # Altera el score del perfil sin tocar un eventual hash de integridad,
    # para dejar evidencia de manipulación en tránsito.
    payload = json.loads(flow.response.content)
    score_original = payload.get("score")
    payload["score"] = 999
    flow.response.content = json.dumps(payload).encode("utf-8")

    customer_id = payload.get("customer_id", "desconocido")
    log.warning(
        "MITM altero perfil de customer_id=%s score_original=%s score_nuevo=%s",
        customer_id,
        score_original,
        payload["score"],
    )
