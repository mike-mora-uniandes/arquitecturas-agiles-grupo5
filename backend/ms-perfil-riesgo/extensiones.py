"""Extensiones compartidas del microservicio (sin lógica de negocio)."""
import redis
from celery import Celery

from config import Config

# Instancia de Celery. Los consumidores/publicadores concretos vivirán en el
# paquete 'tareas'. Aquí solo se configura el transporte (RabbitMQ) y la
# política de acuse acordada para el experimento.
celery_app = Celery("ms_perfil_riesgo", broker=Config.RABBITMQ_URL)
celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
)

# Cliente Redis (caché de datos externos / ASR2 e idempotencia).
# La conexión es perezosa: no se abre hasta el primer comando.
redis_client = redis.Redis.from_url(Config.REDIS_URL, decode_responses=True)
