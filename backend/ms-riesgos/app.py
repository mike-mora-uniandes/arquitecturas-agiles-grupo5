"""Punto de entrada HTTP de MS Riesgos (andamiaje).

Sin endpoints por ahora: el servicio solo construye y arranca. La recepción de
solicitudes y la publicación al broker se implementarán aparte.
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
