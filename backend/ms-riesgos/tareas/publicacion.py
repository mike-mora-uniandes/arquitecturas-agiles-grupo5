"""Publicación de la solicitud de evaluación a RabbitMQ.

El message contract del servicio se mantiene en inglés y conserva el
`correlation_id` para alinear el flujo con `ProfileEvaluationRequest` y
`ProfileEvaluationResult` del microservicio de perfil de riesgo.
"""
import json

import pika

from config import Config


def publicar_solicitud(solicitud):
    """Publica la solicitud en RabbitMQ como un `ProfileEvaluationRequest`.

    El payload debe incluir `correlation_id`, `cliente_id` y el resto del
    contenido de la petición para que el consumidor pueda correlacionar la
    ejecución completa y responder con el resultado asociado.
    """
    if not isinstance(solicitud, dict):
        raise ValueError("La solicitud debe ser un diccionario JSON")

    if not solicitud.get("correlation_id"):
        raise ValueError("La solicitud debe incluir correlation_id")

    parametros = pika.URLParameters(Config.RABBITMQ_URL)
    conexion = pika.BlockingConnection(parametros)
    canal = conexion.channel()
    canal.queue_declare(queue="profile_evaluation_request", durable=True)
    canal.basic_publish(
        exchange="",
        routing_key="profile_evaluation_request",
        body=json.dumps(solicitud),
        properties=pika.BasicProperties(delivery_mode=2),
    )
    conexion.close()

    return solicitud
