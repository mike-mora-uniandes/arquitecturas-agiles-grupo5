"""Punto de entrada HTTP de MS Audit.

Expone un endpoint de solo lectura sobre los incidentes clasificados (útil
para inspeccionar la evidencia del experimento). La responsabilidad central
—consolidar eventos y clasificar intrusiones— vive en el worker Celery
(tareas/consumidores.py).
"""
from flask import Flask, jsonify
from flask_restful import Api, Resource

from config import Config
from extensiones import Session, inicializar_bd
from logica.modelos import Incidente


class IncidentesRecurso(Resource):
    def get(self):
        session = Session()
        try:
            incidentes = (
                session.query(Incidente)
                .order_by(Incidente.detectado_en.desc())
                .limit(100)
                .all()
            )
            return jsonify([i.to_dict() for i in incidentes])
        finally:
            Session.remove()


def crear_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    inicializar_bd()

    api = Api(app)
    api.add_resource(IncidentesRecurso, "/incidentes")

    @app.get("/salud")
    def salud():
        return {"estado": "ok"}, 200

    return app


app = crear_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
