"""Recursos HTTP de MS PerfilRiesgo (esqueleto)."""
from flask_restful import Resource


class ProfileResource(Resource):
    def get(self, customer_id):
        # Sin persistencia local en el experimento: el perfil vive en Redis y se
        # publica al broker. Este endpoint queda fuera de alcance.
        return {"customer_id": customer_id, "profile": None}, 501
