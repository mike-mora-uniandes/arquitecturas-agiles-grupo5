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
from mitmproxy import http


def response(flow: http.HTTPFlow) -> None:
    if "/perfiles" not in flow.request.path:
        return
    # TODO: parsear flow.response.content (JSON), alterar un campo sensible
    # (ej. "score" o "category") y volver a serializar — sin recalcular el
    # hash de integridad, para que la manipulación sea detectable.
    raise NotImplementedError
