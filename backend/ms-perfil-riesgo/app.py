"""Punto de entrada HTTP de MS PerfilRiesgo.

Por ahora expone solo el health-check; la lógica de evaluación de perfil
(ASR1/ASR2/ASR3) se construirá sobre esta base. El microservicio no persiste
localmente: el perfil vive en Redis y se publica al broker.
"""
from flask import Flask
from flask_restful import Api

from config import Config
from vistas.perfiles_riesgo import HealthResource, ProfileResource


def crear_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    api = Api(app)
    api.add_resource(HealthResource, "/health")
    api.add_resource(ProfileResource, "/profiles/<string:customer_id>")

    return app


app = crear_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
