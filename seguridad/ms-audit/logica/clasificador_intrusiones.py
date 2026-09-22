"""Clasificador de patrones de intrusión (táctica Detect Intrusion).

Correlaciona los eventos de ReporteSesionAccion (ms-identidad) y
ReporteExtraccionPerfilRiesgoCliente (ms-riesgo) para decidir si un patrón
de acceso constituye una intrusión no autorizada (ASR1, confidencialidad).
"""

# TODO: implementar clasificar(evento: dict) -> bool | dict
# Señales candidatas: país/IP simulado del atacante (dummy, no GeoIP real —
# ver ../../seed/), discrepancia entre identidad de sesión y customer_id
# solicitado.
