from unittest.mock import patch

from app import crear_app
from config import Config


def test_post_riesgo_publica_solicitud_con_correlation_id():
    app = crear_app()
    app.testing = True

    payload = {
        "customer_id": "C-1001",
        "requested_by": "locust",
        "scenario": "E0",
    }

    with patch("app.publicar_solicitud") as mock_publicar:
        response = app.test_client().post("/evaluations", json=payload)

    assert response.status_code == 202
    body = response.get_json()
    assert "correlation_id" in body
    assert body["correlation_id"]
    assert body["customer_id"] == "C-1001"
    assert body["estado"] == "aceptado"

    mock_publicar.assert_called_once()
    request_payload = mock_publicar.call_args[0][0]
    assert request_payload["correlation_id"] == body["correlation_id"]
    assert request_payload["customer_id"] == "C-1001"
    assert request_payload["requested_by"] == "locust"
    assert request_payload["scenario"] == "E0"


def test_post_riesgo_rechaza_payload_invalido():
    app = crear_app()
    app.testing = True

    response = app.test_client().post("/evaluations", json={"requested_by": "locust"})

    assert response.status_code == 400
    body = response.get_json()
    assert body["error"] == "customer_id es obligatorio"


@patch("tareas.publicacion.celery_app.send_task")
def test_publicar_solicitud_envia_mensaje_con_correlation_id(mock_send_task):
    from tareas.publicacion import publicar_solicitud

    solicitud = {
        "correlation_id": "corr-123",
        "customer_id": "C-1001",
        "requested_by": "locust",
        "scenario": "E0",
    }

    publicado = publicar_solicitud(solicitud)

    assert publicado == solicitud
    mock_send_task.assert_called_once()
    kwargs = mock_send_task.call_args.kwargs
    assert Config.REQUEST_QUEUE == "profile.request.queue"
    assert Config.RESULT_QUEUE == "profile.result.queue"
    assert kwargs["routing_key"] == "profile.request"
    assert kwargs["exchange"] == "solventa"
    assert mock_send_task.call_args.args[0] == "perfil.evaluate_profile"
    assert mock_send_task.call_args.args[1] == [solicitud]
