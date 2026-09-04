"""Punto de entrada HTTP de MS Notificaciones (andamiaje).

Sin endpoints por ahora: el servicio solo construye y arranca. El consumo del
resultado desde el broker, el reintento y el envío a la Dead-Letter Queue se
implementarán aparte.
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
