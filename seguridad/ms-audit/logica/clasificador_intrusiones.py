"""Clasificador de patrones de intrusión (táctica Detect Intrusion).

Correlaciona los eventos de ReporteSesionAccion (ms-identidad) y
ReporteExtraccionPerfilRiesgoCliente (ms-riesgo) para decidir si un patrón de
acceso constituye una intrusión no autorizada de confidencialidad (ASR1).

Señales de intrusión sobre una sesión (independientes; basta una):
  1. BOLA — sesión validada donde el customer_id del token difiere del
     customer_id solicitado (ms-identidad no compara ambos, es la
     vulnerabilidad deliberada). Un token válido para un cliente usado para
     extraer el perfil de otro.
  2. Comportamiento anómalo — el país o device de la request actual (que viaja
     en el evento) difiere del habitual del actor (customer_id del token),
     sembrado en `comportamiento_habitual` (ver seed/). Detecta el acceso de un
     usuario legítimo desde una ubicación/dispositivo inusual (caso que un
     BOLA no cubre, p. ej. `anomaly_ip` del locustfile).

La intrusión se confirma cuando esa sesión sospechosa se cruza con una
extracción real del mismo customer_id dentro de la ventana de correlación.
"""
from datetime import timedelta

from sqlalchemy import select

from config import Config
from logica.modelos import ComportamientoHabitual, HistorialConexion


def _baseline(session, customer_id):
    """Habitual del actor, o None si no hay línea base sembrada para él."""
    if not customer_id:
        return None
    return session.get(ComportamientoHabitual, customer_id)


def _sesion_es_sospechosa(sesion: HistorialConexion, baseline) -> str | None:
    """Devuelve el motivo (str) si la sesión es sospechosa, o None.

    `baseline` es el ComportamientoHabitual del actor (customer_id del token),
    o None si no está sembrado.
    """
    if not sesion.validado:
        # Un rechazo no es una extracción consumada; no dispara incidente de
        # confidencialidad por sí solo (sí queda registrado en el historial).
        return None

    if (
        sesion.customer_id_token
        and sesion.customer_id_token != sesion.customer_id_solicitado
    ):
        return (
            f"BOLA: token de '{sesion.customer_id_token}' usado para extraer "
            f"el perfil de '{sesion.customer_id_solicitado}'"
        )

    if baseline is not None:
        if baseline.pais_habitual and sesion.pais != baseline.pais_habitual:
            return (
                f"comportamiento anómalo: país '{sesion.pais}' distinto del "
                f"habitual '{baseline.pais_habitual}' de "
                f"'{sesion.customer_id_token}'"
            )
        if baseline.device_habitual and sesion.device != baseline.device_habitual:
            return (
                f"comportamiento anómalo: device '{sesion.device}' distinto del "
                f"habitual '{baseline.device_habitual}' de "
                f"'{sesion.customer_id_token}'"
            )

    return None


def buscar_sesion_sospechosa(session, customer_id: str, referencia):
    """Busca la sesión sospechosa más reciente para `customer_id` dentro de la
    ventana de correlación alrededor de `referencia` (timestamp de la
    extracción). Devuelve (sesion, motivo) o (None, None).
    """
    ventana = timedelta(seconds=Config.VENTANA_CORRELACION_S)
    filas = session.execute(
        select(HistorialConexion)
        .where(HistorialConexion.customer_id_solicitado == customer_id)
        .where(HistorialConexion.reportado_en >= referencia - ventana)
        .where(HistorialConexion.reportado_en <= referencia + ventana)
        .order_by(HistorialConexion.reportado_en.desc())
    ).scalars()

    for sesion in filas:
        baseline = _baseline(session, sesion.customer_id_token)
        motivo = _sesion_es_sospechosa(sesion, baseline)
        if motivo:
            return sesion, motivo
    return None, None
