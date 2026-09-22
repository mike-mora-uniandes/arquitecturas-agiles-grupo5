"""Instrumentación OpenTelemetry de MS Notificaciones.

Emite la métrica de *reacción* del experimento de seguridad:
- tiempo_notificacion_ms (ASR3/ASR4, < 5 s) — desde que ms-audit detectó el
  incidente hasta que ms-notificaciones lo entrega al analista.

Mismo patrón no-op / reset de meter por worker prefork que
../ms-audit/telemetria.py y backend/ms-perfil-riesgo/telemetria.py.
"""
import logging
import os
import socket

from celery.signals import worker_process_init
from opentelemetry import metrics


class _FiltrarDetachRuido(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return "Failed to detach context" not in record.getMessage()


logging.getLogger("opentelemetry.context").addFilter(_FiltrarDetachRuido())


def _crear_instrumentos(meter):
    return {
        "notificacion_ms": meter.create_histogram(
            "tiempo_notificacion_ms", unit="ms",
            description="Latencia de notificación al analista desde la detección (ASR3/ASR4)",
        ),
        # Cumplimiento del ASR de reacción, etiquetado por tipo
        # (confidencialidad = ASR3, integridad = ASR4) y pass=true/false.
        "asr_notificacion_within_total": meter.create_counter(
            "solventa_seguridad_asr_notificacion_within_total", unit="1",
            description="Notificaciones dentro del umbral de reacción (5 s), por tipo",
        ),
    }


_provider = None
_meter = metrics.get_meter("solventa.notificaciones")
globals().update(_crear_instrumentos(_meter))


@worker_process_init.connect(weak=False)
def _reiniciar_meter_provider_por_worker(**_kwargs) -> None:
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
    _meter = _provider.get_meter("solventa.notificaciones")
    globals().update(_crear_instrumentos(_meter))
