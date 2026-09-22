"""Pruebas de la publicación de ReporteExtraccionPerfilRiesgoCliente:
sin broker real (`send_task` mockeado) y sin firma (fuera del punto de
sensibilidad del experimento).
"""
from unittest.mock import patch

from config import Config
from tareas.publicacion import publicar_reporte_extraccion


@patch("tareas.publicacion.celery_app.send_task")
def test_publicar_reporte_extraccion_envia_customer_id_y_timestamp(mock_send_task):
    evento = publicar_reporte_extraccion(customer_id="CLI-0007")

    assert evento["customer_id"] == "CLI-0007"
    assert "reportado_en" in evento
    assert "hash_integridad" not in evento

    mock_send_task.assert_called_once()
    args, kwargs = mock_send_task.call_args
    assert args[0] == Config.EXTRACCION_TASK_NAME
    assert args[1] == [evento]
    assert kwargs["exchange"] == Config.RABBITMQ_EXCHANGE
    assert kwargs["routing_key"] == Config.EXTRACCION_ROUTING_KEY
