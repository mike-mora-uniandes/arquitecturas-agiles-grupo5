"""Punto de entrada HTTP de MS Identidad (andamiaje).

Sin endpoints por ahora. Responsabilidad final: identificar, autenticar y
autorizar a los actores que solicitan un perfil de riesgo (ValidarUsuario),
rechazando a quienes no tengan acceso, y publicar de forma asíncrona el
reporte de sesión/acción hacia MS Audit.
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
