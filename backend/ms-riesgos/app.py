"""Punto de entrada HTTP de MS Riesgos.

Expone el endpoint de evaluación para publicar la solicitud al broker con un
correlation ID.
"""
from datetime import datetime, timezone
from uuid import uuid4

from flask import Flask, request
from flask_restful import Api, Resource

from config import Config
from tareas.publicacion import publicar_solicitud


class RiesgosRecurso(Resource):
    def post(self):
        payload = request.get_json(silent=True) or {}

        if not isinstance(payload, dict):
            return {"error": "payload debe ser un JSON válido"}, 400

        customer_id = payload.get("customer_id") or payload.get("cliente_id")
        if not customer_id:
            return {"error": "customer_id es obligatorio"}, 400

        requested_by = payload.get("requested_by") or payload.get("analista_id")
        scenario = payload.get("scenario")

        correlation_id = str(uuid4())
        solicitud = {
            "correlation_id": correlation_id,
            "customer_id": str(customer_id),
            "requested_by": requested_by,
            "scenario": scenario,
            "tipo_evaluacion": payload.get("tipo_evaluacion", "riesgo"),
            "detalles": payload.get("detalles", {}),
            "solicitado_en": datetime.now(timezone.utc).isoformat(),
        }

        publicar_solicitud(solicitud)

        return {
            "correlation_id": correlation_id,
            "customer_id": solicitud["customer_id"],
            "estado": "aceptado",
            "mensaje": "Solicitud encolada correctamente",
        }, 202


def crear_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    api = Api(app)
    api.add_resource(RiesgosRecurso, "/evaluations", "/riesgos/evaluar")

    return app


app = crear_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
