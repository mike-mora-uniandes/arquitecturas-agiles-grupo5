"""Punto de entrada HTTP de MS Notificaciones (andamiaje).

Expone solo el health-check. El consumo del resultado desde el broker, el
reintento y el envío a la Dead-Letter Queue los implementará el dueño.
"""
from flask import Flask
from flask_restful import Api

from config import Config
from vistas.salud import SaludRecurso


def crear_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    api = Api(app)
    api.add_resource(SaludRecurso, "/health")

    return app


app = crear_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
