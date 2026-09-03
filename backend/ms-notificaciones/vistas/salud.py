"""Health-check de MS Notificaciones."""
from flask_restful import Resource


class SaludRecurso(Resource):
    def get(self):
        return {"servicio": "ms-notificaciones", "estado": "ok"}
