import json
from unittest.mock import patch

from app import crear_app


def test_post_riesgo_publica_solicitud_con_correlation_id():
    app = crear_app()
    app.testing = True

    payload = {
        "cliente_id": "C-1001",
        "analista_id": "A-42",
        "tipo_evaluacion": "riesgo",
        "detalles": {"fuente": "manual"},
    }

    with patch("app.publicar_solicitud") as mock_publicar:
        response = app.test_client().post("/riesgos/evaluar", json=payload)

    assert response.status_code == 202
    body = response.get_json()
    assert "correlation_id" in body
    assert body["correlation_id"]
    assert body["cliente_id"] == "C-1001"
    assert body["estado"] == "aceptado"

    mock_publicar.assert_called_once()
    request_payload = mock_publicar.call_args[0][0]
    assert request_payload["correlation_id"] == body["correlation_id"]
    assert request_payload["cliente_id"] == "C-1001"
    assert request_payload["tipo_evaluacion"] == "riesgo"


def test_post_riesgo_rechaza_payload_invalido():
    app = crear_app()
    app.testing = True

    response = app.test_client().post("/riesgos/evaluar", json={"analista_id": "A-42"})

    assert response.status_code == 400
    body = response.get_json()
    assert body["error"] == "cliente_id es obligatorio"


@patch("tareas.publicacion.pika")
def test_publicar_solicitud_envia_mensaje_con_correlation_id(mock_pika):
    from tareas.publicacion import publicar_solicitud

    solicitud = {
        "correlation_id": "corr-123",
        "cliente_id": "C-1001",
        "analista_id": "A-42",
        "tipo_evaluacion": "riesgo",
        "detalles": {"fuente": "manual"},
    }

    publicado = publicar_solicitud(solicitud)

    assert publicado == solicitud
    mock_pika.BlockingConnection.assert_called_once()
    channel = mock_pika.BlockingConnection.return_value.channel.return_value
    channel.basic_publish.assert_called_once()

    kwargs = channel.basic_publish.call_args.kwargs
    body = json.loads(kwargs["body"])
    assert body["correlation_id"] == "corr-123"
    assert body["cliente_id"] == "C-1001"
    assert kwargs["routing_key"] == "profile_evaluation_request"
