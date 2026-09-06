"""ManejoExcepciones — enmascara el fallo con el respaldo del caché (ASR2).

Nunca lanza excepción: siempre devuelve un resultado controlado.
"""
from logica import cache_externos
from mensajes import SOURCE_CACHE, STATUS_DEGRADED, STATUS_DEGRADED_NO_FALLBACK


def enmascarar(customer_id: str) -> dict:
    perfil = cache_externos.leer(customer_id)
    if perfil is None:
        return {
            "status": STATUS_DEGRADED_NO_FALLBACK,
            "source": SOURCE_CACHE,
            "profile": None,
            "reason": "sin respaldo en caché para el cliente",
        }
    return {
        "status": STATUS_DEGRADED,
        "source": SOURCE_CACHE,
        "profile": {
            "score": perfil["score"],
            "category": perfil["category"],
            "calculated_at": perfil["calculated_at"],
            "model_version": perfil["model_version"],
        },
        "reason": None,
    }
