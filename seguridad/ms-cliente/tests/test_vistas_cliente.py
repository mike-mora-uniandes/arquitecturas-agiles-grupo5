"""Pruebas del endpoint IConsultarPerfilRiesgoService: mapea las excepciones
de la orquestación al código HTTP correcto.
"""
from unittest.mock import patch

import pytest

from app import app as flask_app
from logica.orquestador import IntegridadInvalida, PerfilNoEncontrado, UsuarioNoValidado


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as test_client:
        yield test_client


@patch("vistas.cliente.consultar_perfil_riesgo")
def test_devuelve_401_si_no_validado(mock_consultar, client):
    mock_consultar.side_effect = UsuarioNoValidado("firma inválida")

    response = client.post(
        "/perfil-riesgo", json={"token": "t", "customer_id": "CLI-0007"}
    )

    assert response.status_code == 401


@patch("vistas.cliente.consultar_perfil_riesgo")
def test_devuelve_404_si_perfil_no_existe(mock_consultar, client):
    mock_consultar.side_effect = PerfilNoEncontrado()

    response = client.post(
        "/perfil-riesgo", json={"token": "t", "customer_id": "CLI-0007"}
    )

    assert response.status_code == 404


@patch("vistas.cliente.consultar_perfil_riesgo")
def test_devuelve_502_si_integridad_invalida(mock_consultar, client):
    mock_consultar.side_effect = IntegridadInvalida()

    response = client.post(
        "/perfil-riesgo", json={"token": "t", "customer_id": "CLI-0007"}
    )

    assert response.status_code == 502


@patch("vistas.cliente.consultar_perfil_riesgo")
def test_devuelve_perfil_si_todo_ok(mock_consultar, client):
    mock_consultar.return_value = {"customer_id": "CLI-0007", "puntaje": 80}

    response = client.post(
        "/perfil-riesgo", json={"token": "t", "customer_id": "CLI-0007"}
    )

    assert response.status_code == 200
    assert response.get_json()["customer_id"] == "CLI-0007"
