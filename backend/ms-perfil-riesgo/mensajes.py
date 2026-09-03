"""Parseo y construcción de los mensajes del contrato (DESIGN.md §2.1).

El payload es un objeto JSON; cuando viaja como tarea Celery, este objeto es el
único argumento de `perfil.evaluate_profile`.
"""
from datetime import datetime, timezone

from config import Config

# Enums de negocio.
STATUS_OK = "OK"
STATUS_DEGRADED = "DEGRADED"
STATUS_DEGRADED_NO_FALLBACK = "DEGRADED_NO_FALLBACK"

SOURCE_LIVE = "LIVE"
SOURCE_RETRY = "RETRY"
SOURCE_CACHE = "CACHE"


class MensajeInvalido(Exception):
    """El payload no cumple el contrato mínimo (→ DLQ directo)."""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_request(body) -> dict:
    if not isinstance(body, dict):
        raise MensajeInvalido("el payload no es un objeto JSON")
    for campo in ("correlation_id", "customer_id"):
        if not body.get(campo):
            raise MensajeInvalido(f"falta el campo obligatorio '{campo}'")
    return {
        "schema_version": str(body.get("schema_version", Config.SCHEMA_VERSION)),
        "correlation_id": str(body["correlation_id"]),
        "customer_id": str(body["customer_id"]),
        "requested_by": body.get("requested_by"),
        "requested_at": body.get("requested_at"),
        "traceparent": body.get("traceparent"),
    }


def build_result(req: dict, *, status: str, source: str,
                 profile: dict | None = None, reason: str | None = None) -> dict:
    return {
        "schema_version": Config.SCHEMA_VERSION,
        "correlation_id": req["correlation_id"],
        "customer_id": req["customer_id"],
        "requested_by": req.get("requested_by"),
        "status": status,
        "source": source,
        "profile": profile,
        "reason": reason,
        "evaluated_at": now_iso(),
    }
