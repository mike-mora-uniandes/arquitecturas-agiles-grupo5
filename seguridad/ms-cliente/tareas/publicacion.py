"""Publicación de IntegridadFallida al broker (Celery/Kombu).

Se llama cuando ValidadorIntegridad detecta que el hash del perfil no coincide
(ASR2). Lleva `deteccion_ms` (latencia medida inline por ms-cliente) y
`detectado_en` para que ms-audit emita la métrica de detección y publique la
notificación al analista.
"""
from datetime import datetime, timezone

from config import Config
from extensiones import celery_app


def publicar_integridad_fallida(*, customer_id, deteccion_ms, detalle=None):
    evento = {
        "customer_id": customer_id,
        "deteccion_ms": deteccion_ms,
        "detectado_en": datetime.now(timezone.utc).isoformat(),
        "detalle": detalle
        or "hash de integridad no coincide (manipulación en tránsito)",
    }

    celery_app.send_task(
        Config.INTEGRIDAD_TASK_NAME,
        [evento],
        exchange=Config.RABBITMQ_EXCHANGE,
        routing_key=Config.INTEGRIDAD_ROUTING_KEY,
        retry=True,
    )

    return evento
