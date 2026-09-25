"""GeneradorIntegridad — firma el perfil de riesgo antes de entregarlo a
MS Cliente (par de ValidadorIntegridad, ver ../../ms-cliente/).

No firma el reporte async hacia MS Audit (`tareas/publicacion.py`): el punto
de sensibilidad del experimento (ver ../../README.md) es el perfil de riesgo
entregado a ms-cliente, no ese canal interno de auditoría.
"""
import hashlib
import hmac
import json

from config import Config


def generar_hash(payload: dict) -> str:
    mensaje = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hmac.new(
        Config.INTEGRITY_SECRET.encode("utf-8"), mensaje, hashlib.sha256
    ).hexdigest()
