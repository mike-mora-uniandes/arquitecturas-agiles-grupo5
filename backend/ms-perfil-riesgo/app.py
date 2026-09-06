"""Punto de entrada HTTP de MS PerfilRiesgo.

La evaluación de perfil (ASR1/ASR2/ASR3) ocurre en el worker Celery; esta app
solo expone `GET /profiles/<customer_id>` (501, sin persistencia local: el
perfil vive en Redis y se publica al broker).
"""
from flask import Flask
from flask_restful import Api

from config import Config
from vistas.perfiles_riesgo import ProfileResource


def crear_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    api = Api(app)
    api.add_resource(ProfileResource, "/profiles/<string:customer_id>")

    return app


app = crear_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
