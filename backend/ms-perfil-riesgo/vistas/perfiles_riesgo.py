"""Recursos HTTP de MS PerfilRiesgo (esqueleto)."""
from flask_restful import Resource


class SaludRecurso(Resource):
    def get(self):
        return {"servicio": "ms-perfil-riesgo", "estado": "ok"}


class PerfilRiesgoRecurso(Resource):
    def get(self, cliente_id):
        # TODO: devolver el último perfil de riesgo calculado del cliente.
        return {"cliente_id": cliente_id, "perfil": None}, 501
