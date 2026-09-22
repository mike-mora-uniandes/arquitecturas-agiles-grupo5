"""GestionClientes — orquesta el flujo: valida al actor con MS Identidad y,
si es válido, solicita el perfil a MS Riesgo y verifica su hash de
integridad (ValidadorIntegridad) antes de entregarlo.

No repite la verificación de permisos que MS Identidad deliberadamente no
hace (BOLA — ver ../../ms-identidad/README.md, ASR1/ASR3 de
confidencialidad): si `validado` es `true`, se confía en esa respuesta tal
cual. La detección de esa anomalía es responsabilidad de `ms-audit` aguas
abajo, no de este servicio.
"""
from config import Config
from extensiones import sesion_http
from logica.validador_integridad import verificar_hash


class UsuarioNoValidado(Exception):
    def __init__(self, detalle):
        super().__init__(detalle)
        self.detalle = detalle


class PerfilNoEncontrado(Exception):
    pass


class IntegridadInvalida(Exception):
    pass


def consultar_perfil_riesgo(
    *, token, customer_id_solicitado, ip=None, device=None, pais=None
):
    respuesta_identidad = sesion_http.post(
        f"{Config.MS_IDENTIDAD_URL}/validar-usuario",
        json={
            "token": token,
            "customer_id_solicitado": customer_id_solicitado,
            "ip": ip,
            "device": device,
            "pais": pais,
        },
        timeout=5,
    )
    cuerpo_identidad = respuesta_identidad.json()
    if not cuerpo_identidad.get("validado"):
        raise UsuarioNoValidado(cuerpo_identidad.get("error", "usuario no validado"))

    respuesta_riesgo = sesion_http.get(
        f"{Config.MS_RIESGO_URL}/perfiles/{customer_id_solicitado}", timeout=5
    )
    if respuesta_riesgo.status_code == 404:
        raise PerfilNoEncontrado()
    respuesta_riesgo.raise_for_status()

    perfil = respuesta_riesgo.json()
    hash_recibido = perfil.pop("hash_integridad")
    if not verificar_hash(perfil, hash_recibido):
        raise IntegridadInvalida()

    perfil["hash_integridad"] = hash_recibido
    return perfil
