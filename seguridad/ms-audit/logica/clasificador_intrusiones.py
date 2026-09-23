"""Clasificador de patrones de intrusión (táctica Detect Intrusion).

Correlaciona los eventos de ReporteSesionAccion (ms-identidad) y
ReporteExtraccionPerfilRiesgoCliente (ms-riesgo) para decidir si un patrón de
acceso constituye una intrusión no autorizada de confidencialidad (ASR1).

Señales de intrusión sobre una sesión (independientes; basta una):
  1. BOLA — sesión validada donde el customer_id del token difiere del
     customer_id solicitado (ms-identidad no compara ambos, es la
     vulnerabilidad deliberada). Un token válido para un cliente usado para
     extraer el perfil de otro.
  2. Contexto anómalo — país o device en la lista de bloqueo (dummy del
     atacante: país "IR", device "unknown-device"). Cubre el caso en que el
     atacante forja un token que se hace pasar por la propia víctima (mismo
     customer_id en token y solicitud, sin mismatch), detectable solo por su
     origen anómalo.

La intrusión se confirma cuando esa sesión sospechosa se cruza con una
extracción real del mismo customer_id dentro de la ventana de correlación.

NOTA de coordinación (equipo): las dos señales cubren las dos formas en que
hoy se materializa el ataque de confidencialidad entre las ramas de Lorena
(forjar_token: token=víctima, detectable por contexto) y la narrativa BOLA de
ms-identidad (token≠solicitado). Ver README de ms-audit.
"""
from datetime import timedelta

from sqlalchemy import select

from config import Config
from logica.modelos import HistorialConexion


def _sesion_es_sospechosa(sesion: HistorialConexion) -> str | None:
    """Devuelve el motivo (str) si la sesión es sospechosa, o None."""
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
    if sesion.pais in Config.PAISES_ANOMALOS:
        return f"origen anómalo: país '{sesion.pais}'"
    if sesion.device in Config.DEVICES_ANOMALOS:
        return f"origen anómalo: device '{sesion.device}'"
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
        motivo = _sesion_es_sospechosa(sesion)
        if motivo:
            return sesion, motivo
    return None, None
