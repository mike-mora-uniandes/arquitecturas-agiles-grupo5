"""Punto de entrada HTTP de MS Riesgo (andamiaje).

Sin endpoints por ahora. Responsabilidad final: custodiar y entregar el
perfil de riesgo del cliente junto con evidencia verificable de su
integridad (GeneradorIntegridad), y dejar registro de cada extracción de
perfil atendida.
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
