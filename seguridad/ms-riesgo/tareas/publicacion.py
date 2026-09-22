"""Publicación de ReporteExtraccionPerfilRiesgoCliente al broker
(Celery/Kombu). Se publica sin firma — ver nota en
../logica/generador_integridad.py.
"""
from datetime import datetime, timezone

from config import Config
from extensiones import celery_app


def publicar_reporte_extraccion(*, customer_id):
    """Se llama en cada extracción de perfil atendida (ver
    ../vistas/riesgo.py) para que ms-audit pueda correlacionar patrones de
    acceso (ASR1, confidencialidad).
    """
    evento = {
        "customer_id": customer_id,
        "reportado_en": datetime.now(timezone.utc).isoformat(),
    }

    celery_app.send_task(
        Config.EXTRACCION_TASK_NAME,
        [evento],
        exchange=Config.RABBITMQ_EXCHANGE,
        routing_key=Config.EXTRACCION_ROUTING_KEY,
        retry=True,
    )

    return evento
