"""Exception Detection (ASR1) — vocabulario de clasificación de fallos y las
excepciones que lo transportan hacia la capa de reintento (ASR3).
"""

OK = "ok"
TIMEOUT = "timeout"
CONNECTION = "connection"
HTTP_5XX = "http_5xx"
ANOMALOUS = "anomalous"

REINTENTABLES = {TIMEOUT, CONNECTION, HTTP_5XX}


class FalloReintentable(Exception):
    """Fallo transitorio de una fuente externa: se puede reintentar (ASR3)."""

    def __init__(self, clase: str):
        super().__init__(clase)
        self.clase = clase


class RespuestaAnomala(Exception):
    """Respuesta que rompe el contrato: NO se reintenta → va a enmascaramiento."""

    def __init__(self, detalle: str):
        super().__init__(detalle)
        self.clase = ANOMALOUS
        self.detalle = detalle
