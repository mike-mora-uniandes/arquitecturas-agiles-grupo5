"""Emparejamiento sesión↔extracción por request_id + evaluación con el detector.

Cada request es una extracción; su evento de sesión (ms-identidad) y su evento
de extracción (ms-riesgo) comparten un `request_id`. Aquí se recupera la sesión
de una request y se delega la decisión de intrusión al detector heurístico
(logica/detector.py).
"""
from logica.detector import evaluar
from logica.modelos import HistorialConexion


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
    """Empareja la extracción con su sesión por `request_id` y devuelve
    (sesion, motivo) si es intrusión, o (None, None) si la sesión no llegó
    todavía o no es sospechosa.
    """
    sesion = sesion_de_request(session, request_id)
    if sesion is None:
        return None, None
    es_intrusion, _score, motivos = evaluar(session, sesion)
    if not es_intrusion:
        return None, None
    return sesion, "; ".join(motivos)
