"""ValidadorIntegridad — recalcula y compara el hash del perfil de riesgo
recibido de MS Riesgo (par de GeneradorIntegridad, ver ../../ms-riesgo/).

Detecta el ataque de integridad (ASR2): si el hash no coincide, el perfil se
considera manipulado en tránsito (ej. por mitmproxy) y no se entrega como
válido.
"""
import hashlib
import hmac
import json

from config import Config


def verificar_hash(payload: dict, hash_recibido: str) -> bool:
    mensaje = json.dumps(payload, sort_keys=True).encode("utf-8")
    hash_calculado = hmac.new(
        Config.INTEGRITY_SECRET.encode("utf-8"), mensaje, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(hash_calculado, hash_recibido)
