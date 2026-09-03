"""Health-check de MS Riesgos."""
from flask_restful import Resource


class SaludRecurso(Resource):
    def get(self):
        return {"servicio": "ms-riesgos", "estado": "ok"}
