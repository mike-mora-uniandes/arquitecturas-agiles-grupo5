"""Tarea Celery `perfil.evaluate_profile` — flujo completo de DESIGN.md §1.4."""
import json
import logging
import time

from celery.exceptions import Reject

import extensiones
from config import Config
from extensiones import celery_app
from logica import calculo_perfil, cache_externos, manejo_excepciones
from logica.consulta_perfil import consultar_perfil
from mensajes import (
    SOURCE_LIVE,
    SOURCE_RETRY,
    STATUS_OK,
    MensajeInvalido,
    build_result,
    now_iso,
    parse_request,
)
from tareas.publicador import publicar_resultado
from telemetria import asr1_within_threshold_total
from telemetria import evaluation_ms as m_eval_ms
from telemetria import evaluation_total as m_eval_total
from telemetria import tracer

log = logging.getLogger(__name__)

_PROCESSED = "processed:{}"


@celery_app.task(bind=True, name="perfil.evaluate_profile")
def evaluate_profile(self, body):
    try:
        req = parse_request(body)
    except MensajeInvalido as exc:
        log.warning("Mensaje inválido → DLQ: %s", exc)
        raise Reject(str(exc), requeue=False)

    cid = req["correlation_id"]
    with tracer.start_as_current_span("profile.evaluation") as span:
        span.set_attribute("solventa.correlation_id", cid)
        span.set_attribute("solventa.customer_id", req["customer_id"])
        inicio = time.monotonic()

        previo = extensiones.redis_client.get(_PROCESSED.format(cid))
        if previo is not None:
            publicar_resultado(json.loads(previo))
            span.set_attribute("solventa.status", "REPUBLISHED")
            return "republished"

        try:
            resultado = _evaluar(req)
        except Exception as exc:  # bug / infra caída → a la DLQ (sin reencolar)
            log.exception("Error no controlado evaluando %s", cid)
            span.record_exception(exc)
            raise Reject(f"error no controlado: {exc}", requeue=False)

        publicar_resultado(resultado)
        extensiones.redis_client.set(
            _PROCESSED.format(cid), json.dumps(resultado), ex=Config.PROCESSED_TTL_S
        )

        eval_ms = (time.monotonic() - inicio) * 1000
        m_eval_ms.record(eval_ms)
        m_eval_total.add(
            1, {"status": resultado["status"], "source": resultado["source"]}
        )
        span.set_attribute("solventa.status", resultado["status"])
        span.set_attribute("solventa.source", resultado["source"])
        return resultado["status"]


def _evaluar(req: dict) -> dict:
    customer_id = req["customer_id"]
    outcomes = consultar_perfil(customer_id)
    od, ofin = outcomes["open_data"], outcomes["open_finance"]

    detecciones = [o.detection_ms for o in (od, ofin) if o.detection_ms is not None]
    if detecciones:
        dentro = min(detecciones) < Config.DETECTION_TIMEOUT_MS
        asr1_within_threshold_total.add(1, {"pass": str(dentro).lower()})

    if od.ok and ofin.ok:
        perfil = calculo_perfil.calcular(od.data, ofin.data)
        con_reintento = od.attempts > 1 or ofin.attempts > 1
        cache_externos.escribir(
            customer_id, perfil, req["correlation_id"],
            {"open_data": "ok", "open_finance": "ok"},
        )
        return build_result(
            req,
            status=STATUS_OK,
            source=SOURCE_RETRY if con_reintento else SOURCE_LIVE,
            profile={
                "score": perfil["score"],
                "category": perfil["category"],
                "calculated_at": now_iso(),
                "model_version": Config.MODEL_VERSION,
            },
        )

    degradado = manejo_excepciones.enmascarar(customer_id)
    return build_result(
        req,
        status=degradado["status"],
        source=degradado["source"],
        profile=degradado["profile"],
        reason=degradado["reason"],
    )
