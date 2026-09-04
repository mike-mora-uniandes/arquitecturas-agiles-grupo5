"""ConsultaPerfil — llamadas concurrentes a las fuentes externas con detección
(ASR1) y reintentos (ASR3) acotados por un presupuesto de tiempo común.
"""
import contextvars
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from tenacity import (
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    stop_after_delay,
    wait_random_exponential,
)

from config import Config
from logica import fuentes_externas as fx
from logica.deteccion_excepciones import FalloReintentable, RespuestaAnomala
from telemetria import asr3_within_budget_total
from telemetria import detection_ms as m_detection_ms
from telemetria import retry_attempts as m_retry_attempts
from telemetria import retry_ms as m_retry_ms
from telemetria import tracer


@dataclass
class ResultadoFuente:
    system: str
    ok: bool
    data: dict | None
    attempts: int
    retry_ms: float
    first_detection: str | None      # clase del primer fallo detectado
    detection_ms: float | None       # latencia hasta ese primer fallo


def _consultar_fuente(system: str, customer_id: str, deadline: float) -> ResultadoFuente:
    timeout_s = Config.DETECTION_TIMEOUT_MS / 1000
    estado = {"attempts": 0, "first_detection": None, "detection_ms": None}
    inicio = time.monotonic()

    def _intento():
        estado["attempts"] += 1
        t0 = time.monotonic()
        with tracer.start_as_current_span("profile.detection") as sp:
            sp.set_attribute("solventa.source_system", system)
            try:
                data = fx.consultar(system, customer_id, timeout_s)
                sp.set_attribute("solventa.detection.result", "ok")
                sp.set_attribute("solventa.detection.ms", (time.monotonic() - t0) * 1000)
                return data
            except (FalloReintentable, RespuestaAnomala) as exc:
                ms = (time.monotonic() - t0) * 1000
                sp.set_attribute("solventa.detection.result", exc.clase)
                sp.set_attribute("solventa.detection.ms", ms)
                if estado["first_detection"] is None:
                    estado["first_detection"] = exc.clase
                    estado["detection_ms"] = ms
                    m_detection_ms.record(
                        ms, {"source_system": system, "result": exc.clase}
                    )
                raise

    restante = max(0.001, deadline - time.monotonic())
    reintentador = Retrying(
        retry=retry_if_exception_type(FalloReintentable),
        wait=wait_random_exponential(
            multiplier=Config.RETRY_BACKOFF_BASE_MS / 1000, max=restante
        ),
        stop=(stop_after_attempt(Config.RETRY_MAX) | stop_after_delay(restante)),
        reraise=True,
    )

    with tracer.start_as_current_span("profile.retry") as rsp:
        rsp.set_attribute("solventa.source_system", system)
        ok, data = False, None
        try:
            data = reintentador(_intento)
            ok = True
        except (FalloReintentable, RespuestaAnomala):
            ok = False
        retry_total = (time.monotonic() - inicio) * 1000
        rsp.set_attribute("solventa.retry.attempts", estado["attempts"])
        rsp.set_attribute("solventa.retry.ms", retry_total)
        rsp.set_attribute("solventa.retry.exhausted", not ok)
        if estado["attempts"] > 1:
            m_retry_ms.record(retry_total, {"source_system": system})
            m_retry_attempts.record(estado["attempts"], {"source_system": system})
            asr3_within_budget_total.add(
                1, {"pass": str(retry_total <= Config.RETRY_BUDGET_MS).lower()}
            )

    return ResultadoFuente(
        system, ok, data, estado["attempts"], retry_total,
        estado["first_detection"], estado["detection_ms"],
    )


def consultar_perfil(customer_id: str) -> dict:
    """Devuelve {'open_data': ResultadoFuente, 'open_finance': ResultadoFuente}."""
    deadline = time.monotonic() + Config.RETRY_BUDGET_MS / 1000

    def _run(system: str) -> ResultadoFuente:
        return _consultar_fuente(system, customer_id, deadline)

    with ThreadPoolExecutor(max_workers=2) as pool:
        # copy_context() propaga el contexto OTel al hilo → los spans hijos
        # (profile.detection / profile.retry) cuelgan de profile.evaluation.
        futuros = {
            s: pool.submit(contextvars.copy_context().run, _run, s)
            for s in ("open_data", "open_finance")
        }
        return {s: f.result() for s, f in futuros.items()}
