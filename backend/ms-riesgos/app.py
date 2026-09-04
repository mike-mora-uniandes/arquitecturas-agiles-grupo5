"""Punto de entrada HTTP de MS Riesgos.

<<<<<<< HEAD
Expone el health-check y el endpoint de evaluación para publicar la solicitud
al broker con un correlation ID.
"""
from datetime import datetime, timezone
from uuid import uuid4

from flask import Flask, request
from flask_restful import Api, Resource

from config import Config
from tareas.publicacion import publicar_solicitud
from vistas.salud import SaludRecurso
=======
Sin endpoints por ahora: el servicio solo construye y arranca. La recepción de
solicitudes y la publicación al broker se implementarán aparte.
"""
from flask import Flask

from config import Config
>>>>>>> develop


class RiesgosRecurso(Resource):
    def post(self):
        # Contrato HTTP del microservicio: el analista envía la evaluación y el
        # servicio genera un correlation_id para seguir la solicitud completa desde
        # la entrada REST hasta la publicación en RabbitMQ.
        payload = request.get_json(silent=True) or {}

        if not isinstance(payload, dict):
            return {"error": "payload debe ser un JSON válido"}, 400

        cliente_id = payload.get("cliente_id")
        if not cliente_id:
            return {"error": "cliente_id es obligatorio"}, 400

        correlation_id = str(uuid4())
        solicitud = {
            "correlation_id": correlation_id,
            "cliente_id": str(cliente_id),
            "analista_id": payload.get("analista_id"),
            "tipo_evaluacion": payload.get("tipo_evaluacion", "riesgo"),
            "detalles": payload.get("detalles", {}),
            "solicitado_en": datetime.now(timezone.utc).isoformat(),
        }

        publicar_solicitud(solicitud)

        return {
            "correlation_id": correlation_id,
            "cliente_id": solicitud["cliente_id"],
            "estado": "aceptado",
            "mensaje": "Solicitud encolada correctamente",
        }, 202


def crear_app():
    app = Flask(__name__)
    app.config.from_object(Config)

<<<<<<< HEAD
    api = Api(app)
    api.add_resource(SaludRecurso, "/health")
    api.add_resource(RiesgosRecurso, "/riesgos/evaluar")

=======
>>>>>>> develop
    return app


app = crear_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
