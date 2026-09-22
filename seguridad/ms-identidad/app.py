"""Punto de entrada HTTP de MS Identidad.

Expone `ValidarUsuario`, el único endpoint que llama `ms-cliente` antes de
pedir un perfil de riesgo. Sin persistencia de sesión/login real: el
login/auth es dummy a propósito (ver README).
"""
from flask import Flask
from flask_restful import Api

from config import Config
from extensiones import engine, esperar_bd
from logica.modelos import Base
from vistas.identidad import ValidarUsuarioRecurso


def crear_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    esperar_bd(engine)
    Base.metadata.create_all(engine)

    api = Api(app)
    api.add_resource(ValidarUsuarioRecurso, "/validar-usuario")

    return app


app = crear_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
