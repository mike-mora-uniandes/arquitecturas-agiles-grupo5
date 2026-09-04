"""Instrumentación OpenTelemetry de MS PerfilRiesgo (DESIGN.md §2.4).

Con `OTEL_SDK_DISABLED=true` (valor por defecto fuera del experimento) el tracer
y el meter son *no-op*: el código de negocio no cambia.
"""
import logging

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
_meter = metrics.get_meter("solventa.perfil")

# Latencias (ms).
detection_ms = _meter.create_histogram(
    "solventa_profile_detection_ms", unit="ms",
    description="Latencia de detección del primer fallo de una fuente externa (ASR1)",
)
retry_ms = _meter.create_histogram(
    "solventa_profile_retry_ms", unit="ms",
    description="Duración total de los reintentos hacia una fuente externa (ASR3)",
)
retry_attempts = _meter.create_histogram(
    "solventa_profile_retry_attempts", unit="1",
    description="Número de intentos hacia una fuente externa (ASR3)",
)
cache_ms = _meter.create_histogram(
    "solventa_profile_cache_ms", unit="ms",
    description="Latencia del GET al caché de respaldo (ASR2)",
)
evaluation_ms = _meter.create_histogram(
    "solventa_profile_evaluation_ms", unit="ms",
    description="Duración extremo a extremo de una evaluación de perfil",
)

# Contadores.
cache_hit_total = _meter.create_counter("solventa_profile_cache_hit_total", unit="1")
evaluation_total = _meter.create_counter("solventa_profile_evaluation_total", unit="1")

# Señales directas de cumplimiento de ASR (DESIGN.md §3).
asr1_within_threshold_total = _meter.create_counter(
    "solventa_profile_asr1_within_threshold_total", unit="1"
)
asr2_within_threshold_total = _meter.create_counter(
    "solventa_profile_asr2_within_threshold_total", unit="1"
)
asr3_within_budget_total = _meter.create_counter(
    "solventa_profile_asr3_within_budget_total", unit="1"
)
