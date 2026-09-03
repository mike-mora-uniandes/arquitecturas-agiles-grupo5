"""Consumidor Celery del mensaje SolicitudEvaluacionPerfil.

Pendiente de implementar. No incluido en esta entrega de estructura base;
el worker todavía no se arranca en run.sh.
"""
from extensiones import celery_app  # noqa: F401

# TODO: @celery_app.task(bind=True, max_retries=Config.RETRY_MAX)
#       def evaluar_perfil(self, solicitud): ...
#       (detección + retry con backoff + degradación a caché + publicar resultado)
