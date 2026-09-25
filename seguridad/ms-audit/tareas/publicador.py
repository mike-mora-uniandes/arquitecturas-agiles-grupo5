"""Publicación de NotificacionIncidenteSeguridad al broker (Celery/Kombu).

Se llama cuando el clasificador confirma una intrusión. Lo consume
ms-notificaciones (ASR3/ASR4 — reacción). El evento lleva `detectado_en` para
que ms-notificaciones pueda medir `tiempo_notificacion_ms` desde la detección.
"""
from config import Config
from extensiones import celery_app


def publicar_incidente(incidente: dict):
    """`incidente` es el dict de logica.modelos.Incidente.to_dict()."""
    celery_app.send_task(
        Config.NOTIFICAR_INCIDENTE_TASK_NAME,
        [incidente],
        exchange=Config.RABBITMQ_EXCHANGE,
        routing_key=Config.INCIDENTE_ROUTING_KEY,
        retry=True,
    )
    return incidente
