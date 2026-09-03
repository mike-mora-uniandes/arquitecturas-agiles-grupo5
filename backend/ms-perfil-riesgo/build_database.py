"""Crea el esquema local del microservicio."""
from app import app
from extensiones import db

with app.app_context():
    db.create_all()
    print("Esquema de MS PerfilRiesgo creado.")
