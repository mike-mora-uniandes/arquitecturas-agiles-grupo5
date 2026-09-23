"""Clasificador de patrones de intrusión (táctica Detect Intrusion).

Modelo simple y exacto: **cada request es una extracción**, y su evento de
sesión (ms-identidad) y su evento de extracción (ms-riesgo) comparten un
`request_id` generado por ms-cliente. ms-audit empareja ambos por ese id —
sin ventanas ni agrupación — y decide si esa request fue una intrusión.

Una request es intrusión de confidencialidad si su sesión (validada) es
sospechosa por:
  1. BOLA — el customer_id del token difiere del solicitado (ms-identidad no
     los compara: la vulnerabilidad deliberada).
  2. Comportamiento anómalo — el país o device de la request difiere del
     habitual del actor (tabla comportamiento_habitual, sembrada por seed/).

Cada extracción no autorizada cuenta como su propio incidente; una extracción
legítima (su sesión coincide con el habitual) no se marca.
"""
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


def sesion_de_request(session, request_id: str):
    """La sesión (HistorialConexion) de esa request, o None si aún no llegó."""
    if not request_id:
        return None
    return (
        session.query(HistorialConexion)
        .filter_by(request_id=request_id)
        .order_by(HistorialConexion.id.desc())
        .first()
    )


def evaluar_request(session, request_id: str):
    """Empareja la extracción con su sesión por `request_id` y devuelve el
    motivo de intrusión, o None si la sesión no llegó todavía o no es
    sospechosa.
    """
    sesion = sesion_de_request(session, request_id)
    if sesion is None:
        return None
    return _sesion_es_sospechosa(sesion, _baseline(session, sesion.customer_id_token))
