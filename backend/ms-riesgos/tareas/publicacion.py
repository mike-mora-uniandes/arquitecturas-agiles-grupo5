"""Publicación de la solicitud de evaluación al broker Celery/Kombu."""
from config import Config
from extensiones import celery_app


def publicar_solicitud(solicitud):
    """Publica la solicitud en la cola de trabajo del perfil de riesgo."""
    if not isinstance(solicitud, dict):
        raise ValueError("La solicitud debe ser un diccionario JSON")

    if not solicitud.get("correlation_id"):
        raise ValueError("La solicitud debe incluir correlation_id")

    celery_app.send_task(
        "perfil.evaluate_profile",
        [solicitud],
        exchange=Config.RABBITMQ_EXCHANGE,
        routing_key=Config.REQUEST_ROUTING_KEY,
        retry=True,
    )

    return solicitud
