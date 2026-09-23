"""GestionClientes — orquesta el flujo: valida al actor con MS Identidad y,
si es válido, solicita el perfil a MS Riesgo y verifica su hash de
integridad (ValidadorIntegridad) antes de entregarlo.

No repite la verificación de permisos que MS Identidad deliberadamente no
hace (BOLA — ver ../../ms-identidad/README.md, ASR1/ASR3 de
confidencialidad): si `validado` es `true`, se confía en esa respuesta tal
cual. La detección de esa anomalía es responsabilidad de `ms-audit` aguas
abajo, no de este servicio.

La integridad (ASR2) sí se detecta aquí, inline: si el hash del perfil no
coincide, se mide la latencia de detección y se publica IntegridadFallida al
broker para que ms-audit emita la métrica y notifique (ver
tareas/publicacion.py y ../ms-audit/README.md).
"""
import time

from config import Config
from extensiones import sesion_http
from logica.validador_integridad import verificar_hash
from tareas.publicacion import publicar_integridad_fallida


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

    # t0 de ASR2: desde que se pide el perfil a ms-riesgo (donde podría
    # alterarse en tránsito, p. ej. por mitmproxy) hasta que se detecta el
    # hash inconsistente al verificarlo.
    solicitado_en = time.monotonic()
    respuesta_riesgo = sesion_http.get(
        f"{Config.MS_RIESGO_URL}/perfiles/{customer_id_solicitado}", timeout=5
    )
    if respuesta_riesgo.status_code == 404:
        raise PerfilNoEncontrado()
    respuesta_riesgo.raise_for_status()

    perfil = respuesta_riesgo.json()
    hash_recibido = perfil.pop("hash_integridad")
    if not verificar_hash(perfil, hash_recibido):
        deteccion_ms = (time.monotonic() - solicitado_en) * 1000.0
        publicar_integridad_fallida(
            customer_id=customer_id_solicitado, deteccion_ms=deteccion_ms
        )
        raise IntegridadInvalida()

    perfil["hash_integridad"] = hash_recibido
    return perfil
