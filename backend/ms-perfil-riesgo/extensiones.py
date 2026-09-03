"""Extensiones compartidas del microservicio (sin lógica de negocio)."""
from celery import Celery
from flask_sqlalchemy import SQLAlchemy

from config import Config

db = SQLAlchemy()

# Instancia de Celery. Los consumidores/publicadores concretos vivirán en el
# paquete 'tareas'. Aquí solo se configura el transporte (RabbitMQ).
celery_app = Celery("ms_perfil_riesgo", broker=Config.RABBITMQ_URL)
