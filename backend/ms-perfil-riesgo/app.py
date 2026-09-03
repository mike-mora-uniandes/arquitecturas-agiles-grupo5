"""Punto de entrada HTTP de MS PerfilRiesgo.

Por ahora expone solo el health-check; la lógica de evaluación de perfil
(ASR1/ASR2/ASR3) se construirá sobre esta base.
"""
from flask import Flask
from flask_restful import Api

from config import Config
from extensiones import db
from modelos import perfil_riesgo  # noqa: F401  (registra el modelo en db)
from vistas.perfiles_riesgo import PerfilRiesgoRecurso, SaludRecurso


def crear_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    api = Api(app)
    api.add_resource(SaludRecurso, "/health")
    api.add_resource(PerfilRiesgoRecurso, "/perfiles-riesgo/<string:cliente_id>")

    return app


app = crear_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
