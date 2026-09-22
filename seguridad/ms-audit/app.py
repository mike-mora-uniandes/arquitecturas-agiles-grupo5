"""Punto de entrada HTTP de MS Audit (andamiaje).

Sin endpoints propios. Responsabilidad final: consolidar los eventos de
auditoría y clasificar los patrones de acceso que constituyen intrusiones no
autorizadas con riesgo de divulgación indebida de datos.
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
