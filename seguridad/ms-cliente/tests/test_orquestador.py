"""Pruebas de la orquestación MS Identidad -> MS Riesgo: rechazo de
identidad, éxito, perfil no encontrado y hash inválido. `requests` mockeado
(vía `logica.orquestador.sesion_http`) — no necesitan que ms-identidad ni
ms-riesgo estén corriendo.
"""
import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

import pytest

from config import Config
from logica.orquestador import (
    IntegridadInvalida,
    PerfilNoEncontrado,
    UsuarioNoValidado,
    consultar_perfil_riesgo,
)

PERFIL = {
    "customer_id": "CLI-0007",
    "nombre_completo": "Juana Pérez",
    "documento_identidad": "123456",
    "puntaje": 80,
    "categoria": "ALTO",
    "actualizado_en": "2026-01-01T00:00:00+00:00",
}


def _hash_valido(payload):
    mensaje = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hmac.new(
        Config.INTEGRITY_SECRET.encode("utf-8"), mensaje, hashlib.sha256
    ).hexdigest()


def _mock_response(status_code, cuerpo_json):
    respuesta = MagicMock()
    respuesta.status_code = status_code
    respuesta.json.return_value = cuerpo_json
    respuesta.raise_for_status = MagicMock()
    return respuesta


@patch("logica.orquestador.sesion_http")
def test_rechazo_por_identidad_no_llama_a_ms_riesgo(mock_http):
    mock_http.post.return_value = _mock_response(
        401, {"validado": False, "error": "firma inválida"}
    )

    with pytest.raises(UsuarioNoValidado):
        consultar_perfil_riesgo(token="t", customer_id_solicitado="CLI-0007")

    mock_http.get.assert_not_called()


@patch("logica.orquestador.sesion_http")
def test_perfil_valido_se_entrega_con_su_hash(mock_http):
    hash_valido = _hash_valido(PERFIL)
    mock_http.post.return_value = _mock_response(
        200, {"validado": True, "customer_id_token": "CLI-0001"}
    )
    mock_http.get.return_value = _mock_response(
        200, {**PERFIL, "hash_integridad": hash_valido}
    )

    resultado = consultar_perfil_riesgo(token="t", customer_id_solicitado="CLI-0007")

    assert resultado["customer_id"] == "CLI-0007"
    assert resultado["hash_integridad"] == hash_valido


@patch("logica.orquestador.publicar_integridad_fallida")
@patch("logica.orquestador.sesion_http")
def test_hash_alterado_en_transito_se_detecta(mock_http, mock_publicar):
    hash_original = _hash_valido(PERFIL)
    perfil_alterado = {**PERFIL, "puntaje": 999}  # alterado, hash sin recalcular
    mock_http.post.return_value = _mock_response(
        200, {"validado": True, "customer_id_token": "CLI-0001"}
    )
    mock_http.get.return_value = _mock_response(
        200, {**perfil_alterado, "hash_integridad": hash_original}
    )

    with pytest.raises(IntegridadInvalida):
        consultar_perfil_riesgo(token="t", customer_id_solicitado="CLI-0007")

    # Al detectar la manipulación se publica IntegridadFallida hacia ms-audit
    # (ASR2), con el customer_id y una latencia de detección medida.
    mock_publicar.assert_called_once()
    kwargs = mock_publicar.call_args.kwargs
    assert kwargs["customer_id"] == "CLI-0007"
    assert kwargs["deteccion_ms"] >= 0


@patch("logica.orquestador.sesion_http")
def test_perfil_no_encontrado_en_ms_riesgo(mock_http):
    mock_http.post.return_value = _mock_response(
        200, {"validado": True, "customer_id_token": "CLI-0001"}
    )
    mock_http.get.return_value = _mock_response(404, {"error": "no encontrado"})

    with pytest.raises(PerfilNoEncontrado):
        consultar_perfil_riesgo(token="t", customer_id_solicitado="CLI-0007")
