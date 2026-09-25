"""Instrumentación OpenTelemetry de MS Audit.

Emite las métricas de *detección* del experimento de seguridad:
- tiempo_deteccion_confidencialidad_ms (ASR1, < 200 ms) — camino asíncrono
  (broker → clasificación en ms-audit).
- tiempo_deteccion_integridad_ms (ASR2, < 500 ms) — medido inline por
  ms-cliente y reportado en el evento; ms-audit lo centraliza como métrica.

Mismo patrón que backend/ms-perfil-riesgo/telemetria.py: con
`OTEL_SDK_DISABLED=true` (default fuera del experimento) meter e instrumentos
son no-op y el código de negocio no cambia. Cada proceso hijo del pool
prefork de Celery recibe su propia identidad de métricas para que el
Collector agregue N series en vez de pisarlas entre sí.
"""
import logging
import os
import socket

from celery.signals import worker_process_init
from opentelemetry import metrics


class _FiltrarDetachRuido(logging.Filter):
    """opentelemetry-instrumentation-celery 0.48b0 registra de forma espuria
    'Failed to detach context' con el pool prefork (bug conocido de contrib).
    """

    def filter(self, record: logging.LogRecord) -> bool:
        return "Failed to detach context" not in record.getMessage()


logging.getLogger("opentelemetry.context").addFilter(_FiltrarDetachRuido())


def _crear_instrumentos(meter):
    """(Re)crea todos los instrumentos de negocio sobre el `meter` dado."""
    return {
        # Latencias de detección (ms). El exporter Prometheus expone estos
        # histogramas como <nombre>_milliseconds_bucket/_sum/_count.
        "deteccion_confidencialidad_ms": meter.create_histogram(
            "tiempo_deteccion_confidencialidad_ms", unit="ms",
            description="Latencia de detección de la extracción no autorizada (ASR1)",
        ),
        "deteccion_integridad_ms": meter.create_histogram(
            "tiempo_deteccion_integridad_ms", unit="ms",
            description="Latencia de detección de la alteración no autorizada (ASR2)",
        ),
        # Señales directas de cumplimiento de ASR (pass=true/false).
        "asr1_within_threshold_total": meter.create_counter(
            "solventa_seguridad_asr1_within_threshold_total", unit="1",
            description="Detecciones de confidencialidad dentro del umbral ASR1 (200 ms)",
        ),
        "asr2_within_threshold_total": meter.create_counter(
            "solventa_seguridad_asr2_within_threshold_total", unit="1",
            description="Detecciones de integridad dentro del umbral ASR2 (500 ms)",
        ),
        # Volumen de intrusiones clasificadas, por tipo.
        "intrusiones_total": meter.create_counter(
            "solventa_seguridad_intrusiones_total", unit="1",
            description="Intrusiones clasificadas por ms-audit, por tipo",
        ),
        # Mezcla de tráfico observado por ms-audit, por clase (legitima,
        # acceso_no_autorizado, anomala_comportamiento, rechazada).
        "requests_total": meter.create_counter(
            "solventa_seguridad_requests_total", unit="1",
            description="Requests observadas por ms-audit, por clase de tráfico",
        ),
    }


_provider = None
_meter = metrics.get_meter("solventa.audit")
globals().update(_crear_instrumentos(_meter))


@worker_process_init.connect(weak=False)
def _reiniciar_meter_provider_por_worker(**_kwargs) -> None:
    """Da a cada proceso hijo del pool prefork su propio `service.instance.id`
    y MeterProvider, para que el Collector no pise las series entre workers
    (ver la explicación extendida en backend/ms-perfil-riesgo/telemetria.py).
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
    _meter = _provider.get_meter("solventa.audit")
    globals().update(_crear_instrumentos(_meter))
