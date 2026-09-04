"""CacheExternos — lectura/escritura del respaldo del perfil en Redis (ASR2)."""
import json
import time
from datetime import datetime, timezone

import extensiones
from config import Config
from telemetria import asr2_within_threshold_total
from telemetria import cache_hit_total
from telemetria import cache_ms as m_cache_ms
from telemetria import tracer


def _key(customer_id: str) -> str:
    return f"profile:{customer_id}"


def _age_s(calculated_at) -> float | None:
    if not calculated_at:
        return None
    try:
        t = datetime.fromisoformat(str(calculated_at).replace("Z", "+00:00"))
    except ValueError:
        return None
    return (datetime.now(timezone.utc) - t).total_seconds()


def leer(customer_id: str) -> dict | None:
    with tracer.start_as_current_span("profile.cache_lookup") as sp:
        t0 = time.monotonic()
        crudo = extensiones.redis_client.get(_key(customer_id))
        ms = (time.monotonic() - t0) * 1000
        hit = crudo is not None

        sp.set_attribute("solventa.cache.hit", hit)
        sp.set_attribute("solventa.cache.ms", ms)
        m_cache_ms.record(ms)
        cache_hit_total.add(1, {"hit": str(hit).lower()})
        asr2_within_threshold_total.add(
            1, {"pass": str(ms < Config.CACHE_ASR2_THRESHOLD_MS).lower()}
        )

        if not hit:
            return None

        perfil = json.loads(crudo)
        edad = _age_s(perfil.get("calculated_at"))
        obsoleto = perfil.get("model_version") != Config.MODEL_VERSION
        if edad is not None:
            sp.set_attribute("solventa.cache.age_s", edad)
        sp.set_attribute("solventa.cache.stale_version", obsoleto)
        return perfil


def escribir(customer_id: str, profile: dict, correlation_id: str,
             sources: dict) -> None:
    doc = {
        "customer_id": customer_id,
        "score": profile["score"],
        "category": profile["category"],
        "calculated_at": datetime.now(timezone.utc).isoformat(),
        "model_version": Config.MODEL_VERSION,
        "snapshot_type": "LIVE_EVALUATION",
        "correlation_id": correlation_id,
        "sources": sources,
    }
    extensiones.redis_client.set(
        _key(customer_id), json.dumps(doc), ex=Config.CACHE_TTL_S
    )
