"""Lógica de ValidarUsuario — valida la firma del token y que el titular
exista en GestiónRoles.

Vulnerabilidad deliberada del experimento (ASR1/ASR3, confidencialidad): NO
se compara `customer_id` del token contra `customer_id_solicitado`. Un token
legítimamente firmado para *cualquier* customer_id se acepta como válido
para consultar el perfil de *cualquier otro* customer_id (BOLA). La
detección de esta anomalía no ocurre aquí — ocurre aguas abajo, en
ms-audit, correlacionando ReporteSesionAccion (que sí lleva ambos
customer_id, ver tareas/publicacion.py).
"""
import jwt

from config import Config
from extensiones import Session
from logica.modelos import Usuario


class TokenInvalido(Exception):
    """La firma del token no es válida, o el usuario no existe en GestiónRoles."""


def validar_usuario(token: str, customer_id_solicitado: str) -> dict:
    try:
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
    except jwt.InvalidTokenError as exc:
        raise TokenInvalido(f"firma inválida: {exc}") from exc

    customer_id_token = payload.get("customer_id")
    if not customer_id_token:
        raise TokenInvalido("el token no trae customer_id")

    session = Session()
    try:
        usuario = session.get(Usuario, customer_id_token)
    finally:
        Session.remove()

    if usuario is None:
        raise TokenInvalido(
            f"customer_id '{customer_id_token}' no existe en GestiónRoles"
        )

    return {
        "customer_id_token": customer_id_token,
        "customer_id_solicitado": customer_id_solicitado,
        "rol": usuario.rol,
    }
