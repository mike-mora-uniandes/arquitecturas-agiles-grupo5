"""Publicación de ProfileEvaluationResult hacia MS Notificaciones (DESIGN.md §2.1)."""
from config import Config
from extensiones import celery_app


def publicar_resultado(resultado: dict) -> None:
    # Se envía como tarea Celery (nombre en Config.RESULT_TASK_NAME); el único
    # argumento es el contrato ProfileEvaluationResult. Ruteada al exchange
    # 'solventa' con la routing key 'profile.result'.
    celery_app.send_task(
        Config.RESULT_TASK_NAME,
        args=[resultado],
        exchange=Config.RABBITMQ_EXCHANGE,
        routing_key=Config.RESULT_ROUTING_KEY,
        retry=True,
    )
