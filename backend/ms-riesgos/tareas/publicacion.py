"""Publicación de la solicitud de evaluación a RabbitMQ.

Este módulo mantiene el contrato del microservicio y permite mockear la
función exportada desde app.py para realizar pruebas de integración.
"""


def publicar_solicitud(solicitud):
    """Publica la solicitud en el broker de RabbitMQ.

    El payload debe conservar el contrato `ProfileEvaluationRequest`: incluye el
    `correlation_id` para que el consumidor asociado pueda correlacionar la
    ejecución completa y publicar luego `ProfileEvaluationResult`.

    La implementación real de transporte se dejará para la siguiente iteración.
    Por ahora el contrato y la trazabilidad quedan cubiertos en la firma.
    """
    return solicitud
