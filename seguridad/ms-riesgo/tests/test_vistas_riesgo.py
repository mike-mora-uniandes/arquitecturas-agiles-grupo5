"""Pruebas de SolicitarPerfil: perfil existente (con hash) y no encontrado.

Usa SQLite en memoria en vez de la BD real (Postgres solo existe dentro de
docker compose) y mockea la publicación async — no necesitan broker.
"""
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from flask import Flask
from flask_restful import Api
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from logica.modelos import Base, PerfilRiesgo
from vistas.riesgo import SolicitarPerfilRecurso


@pytest.fixture
def client(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SesionPrueba = scoped_session(sessionmaker(bind=engine))

    sesion = SesionPrueba()
    sesion.add(
        PerfilRiesgo(
            customer_id="CLI-0007",
            nombre_completo="Juana Pérez",
            documento_identidad="123456",
            puntaje=80,
            categoria="ALTO",
            actualizado_en=datetime.now(timezone.utc),
        )
    )
    sesion.commit()
    monkeypatch.setattr("vistas.riesgo.Session", SesionPrueba)

    app = Flask(__name__)
    api = Api(app)
    api.add_resource(SolicitarPerfilRecurso, "/perfiles/<string:customer_id>")
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


@patch("vistas.riesgo.publicar_reporte_extraccion")
def test_solicitar_perfil_existente_devuelve_hash_y_publica_reporte(mock_publicar, client):
    response = client.get(
        "/perfiles/CLI-0007", headers={"X-Request-Id": "req-xyz"}
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["customer_id"] == "CLI-0007"
    assert "hash_integridad" in body
    mock_publicar.assert_called_once_with(
        customer_id="CLI-0007", request_id="req-xyz"
    )


@patch("vistas.riesgo.publicar_reporte_extraccion")
def test_solicitar_perfil_no_encontrado_no_publica_reporte(mock_publicar, client):
    response = client.get("/perfiles/CLI-9999")

    assert response.status_code == 404
    mock_publicar.assert_not_called()
