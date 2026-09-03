"""Consumidor Celery del mensaje ProfileEvaluationRequest.

Pendiente de implementar. No incluido en esta entrega de estructura base;
el contrato de mensajes y la topología RabbitMQ se acordarán con el equipo.
"""
from extensiones import celery_app  # noqa: F401

# TODO: @celery_app.task(bind=True) def evaluate_profile(self, request): ...
#   - idempotencia: SET NX processed:{correlation_id}
#   - ConsultaPerfil: Open Data + Open Finance concurrentes
#   - deteccion_excepciones (ASR1) + retry con tenacity (ASR3)
#   - manejo_excepciones + cache_externos (ASR2)
#   - calculo_perfil -> publicar ProfileEvaluationResult
