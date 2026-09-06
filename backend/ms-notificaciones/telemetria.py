"""Ajustes de OpenTelemetry específicos de MS Notificaciones."""
import logging


class _FiltrarDetachRuido(logging.Filter):
    """opentelemetry-instrumentation-celery 0.48b0 registra de forma espuria
    'Failed to detach context' con el pool prefork (bug conocido de contrib,
    ver ../ms-perfil-riesgo/telemetria.py). Es inocuo; se filtra para no
    ensuciar los logs del worker.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        return "Failed to detach context" not in record.getMessage()


logging.getLogger("opentelemetry.context").addFilter(_FiltrarDetachRuido())
