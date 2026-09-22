"""Punto de entrada HTTP de MS Riesgo.

Expone `SolicitarPerfil`, el único endpoint que llama `ms-cliente` para
obtener el perfil de riesgo del cliente junto con su hash de integridad
(GeneradorIntegridad).
"""
from flask import Flask
from flask_restful import Api

from config import Config
from extensiones import engine, esperar_bd
from logica.modelos import Base
from vistas.riesgo import SolicitarPerfilRecurso


def crear_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    esperar_bd(engine)
    Base.metadata.create_all(engine)

    api = Api(app)
    api.add_resource(SolicitarPerfilRecurso, "/perfiles/<string:customer_id>")

    return app


app = crear_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
