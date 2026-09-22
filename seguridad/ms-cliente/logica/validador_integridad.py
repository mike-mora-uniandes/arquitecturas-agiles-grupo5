"""ValidadorIntegridad — recalcula y compara el hash del perfil de riesgo
recibido de MS Riesgo (par de GeneradorIntegridad, ver ../../ms-riesgo/).

Detecta el ataque de integridad (ASR2): si el hash no coincide, el perfil se
considera manipulado en tránsito (ej. por mitmproxy) y no se entrega como
válido.
"""

# TODO: implementar verificar_hash(payload: dict, hash_recibido: str) -> bool
# usando hashlib/hmac, con la misma clave/algoritmo que GeneradorIntegridad.
