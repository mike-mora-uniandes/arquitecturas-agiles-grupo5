"""Punto de entrada HTTP de MS Cliente.

Expone `IConsultarPerfilRiesgoService` (`/perfil-riesgo`), el punto de
entrada del flujo: orquesta MS Identidad -> MS Riesgo y verifica la
integridad del perfil recibido antes de responder.
"""
from flask import Flask
from flask_restful import Api

from config import Config
from vistas.cliente import ConsultarPerfilRiesgoRecurso


def crear_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    api = Api(app)
    api.add_resource(ConsultarPerfilRiesgoRecurso, "/perfil-riesgo")

    return app


app = crear_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
