"""Instrumentación OpenTelemetry de MS PerfilRiesgo (DESIGN.md §2.4).

Con `OTEL_SDK_DISABLED=true` (valor por defecto fuera del experimento) el tracer
y el meter son *no-op*: el código de negocio no cambia.
"""
import logging
import os
import socket

from celery.signals import worker_process_init
from opentelemetry import metrics, trace


class _FiltrarDetachRuido(logging.Filter):
    """opentelemetry-instrumentation-celery 0.48b0 registra de forma espuria
    'Failed to detach context' con el pool prefork (bug conocido de contrib).
    Es inocuo; se filtra para no ensuciar los logs del worker.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        return "Failed to detach context" not in record.getMessage()


logging.getLogger("opentelemetry.context").addFilter(_FiltrarDetachRuido())

tracer = trace.get_tracer("solventa.perfil")


def _crear_instrumentos(meter):
    """(Re)crea todos los instrumentos de negocio sobre el `meter` dado."""
    return {
        # Latencias (ms).
        "detection_ms": meter.create_histogram(
            "solventa_profile_detection_ms", unit="ms",
            description="Latencia de detección del primer fallo de una fuente externa (ASR1)",
        ),
        "retry_ms": meter.create_histogram(
            "solventa_profile_retry_ms", unit="ms",
            description="Duración total de los reintentos hacia una fuente externa (ASR3)",
        ),
        "retry_attempts": meter.create_histogram(
            "solventa_profile_retry_attempts", unit="1",
            description="Número de intentos hacia una fuente externa (ASR3)",
        ),
        "cache_ms": meter.create_histogram(
            "solventa_profile_cache_ms", unit="ms",
            description="Latencia del GET al caché de respaldo (ASR2)",
        ),
        "evaluation_ms": meter.create_histogram(
            "solventa_profile_evaluation_ms", unit="ms",
            description="Duración extremo a extremo de una evaluación de perfil",
        ),
        # Contadores.
        "cache_hit_total": meter.create_counter(
            "solventa_profile_cache_hit_total", unit="1"
        ),
        "evaluation_total": meter.create_counter(
            "solventa_profile_evaluation_total", unit="1"
        ),
        # Señales directas de cumplimiento de ASR (DESIGN.md §3).
        "asr1_within_threshold_total": meter.create_counter(
            "solventa_profile_asr1_within_threshold_total", unit="1"
        ),
        "asr2_within_threshold_total": meter.create_counter(
            "solventa_profile_asr2_within_threshold_total", unit="1"
        ),
        "asr3_within_budget_total": meter.create_counter(
            "solventa_profile_asr3_within_budget_total", unit="1"
        ),
    }


_provider = None  # solo se usa si `_reiniciar_meter_provider_por_worker` corre
_meter = metrics.get_meter("solventa.perfil")
globals().update(_crear_instrumentos(_meter))


@worker_process_init.connect(weak=False)
def _reiniciar_meter_provider_por_worker(**_kwargs) -> None:
    """Da a cada proceso hijo del pool prefork de Celery su propia identidad
    de métricas (DESIGN.md §2.4 / issue: contadores cruzados entre workers).

    `--concurrency` forkea N procesos hijo; cada uno hereda por fork el mismo
    MeterProvider y las mismas Resource attributes creadas en el proceso
    padre (antes del fork), pero mantiene su propio conteo en memoria. Como
    todos exportan bajo la misma identidad de serie (mismos atributos de
    resource, sin distinguir proceso), el OTel Collector no las suma: expone
    el último valor recibido de cualquiera de los workers, así que la serie
    visible en Prometheus "salta" entre los conteos independientes de cada
    proceso en lugar de acumularlos.

    Se corrige dando a cada hijo, tras el fork, un `service.instance.id`
    propio (host + PID) y un MeterProvider/exportador nuevos; así el
    Collector ve N series distintas y los `sum(...)` de los dashboards
    agregan correctamente. Si el SDK está deshabilitado no hay nada que
    reiniciar (meter/instrumentos ya son no-op).

    El nuevo MeterProvider se usa de forma local (no se registra vía
    `metrics.set_meter_provider`): la API global solo admite fijar el
    provider una vez por proceso, y ese fork ya lo hereda como "fijado"
    desde el proceso padre, así que un segundo intento no tendría efecto
    (queda descartado en silencio, solo con un warning). Como todo el
    código de negocio referencia los instrumentos vía el módulo
    `telemetria` (no vía `metrics.get_meter()`), basta con reasignar los
    globales para que apunten al meter del nuevo provider.
    """
    if os.environ.get("OTEL_SDK_DISABLED", "false").lower() == "true":
        return

    from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
        OTLPMetricExporter,
    )
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource

    instance_id = f"{socket.gethostname()}-{os.getpid()}"
    resource = Resource.create().merge(
        Resource.create({"service.instance.id": instance_id})
    )
    export_interval_ms = int(os.environ.get("OTEL_METRIC_EXPORT_INTERVAL", "60000"))
    reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(), export_interval_millis=export_interval_ms
    )

    global _provider, _meter
    _provider = MeterProvider(resource=resource, metric_readers=[reader])
    _meter = _provider.get_meter("solventa.perfil")
    globals().update(_crear_instrumentos(_meter))
