"""Punto de entrada HTTP de MS Notificaciones (andamiaje).

Sin endpoints propios. Responsabilidad final: informar a los actores
responsables (analista de riesgo) los incidentes de seguridad identificados
en el sistema.
"""
from flask import Flask

from config import Config


def crear_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    return app


app = crear_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
