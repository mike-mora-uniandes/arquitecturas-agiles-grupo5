"""Endpoint SolicitarPerfil — lo llama ms-cliente para obtener el perfil de
riesgo junto con su hash de integridad.
"""
from flask import request
from flask_restful import Resource

from extensiones import Session
from logica.generador_integridad import generar_hash
from logica.modelos import PerfilRiesgo
from tareas.publicacion import publicar_reporte_extraccion


class SolicitarPerfilRecurso(Resource):
    def get(self, customer_id):
        session = Session()
        try:
            perfil = session.get(PerfilRiesgo, customer_id)
        finally:
            Session.remove()

        if perfil is None:
            return {"error": f"perfil '{customer_id}' no encontrado"}, 404

        datos = perfil.to_dict()
        datos["hash_integridad"] = generar_hash(datos)

        # request_id lo propaga ms-cliente por header para que ms-audit empareje
        # esta extracción con su sesión (cada request es una extracción).
        publicar_reporte_extraccion(
            customer_id=customer_id, request_id=request.headers.get("X-Request-Id")
        )

        return datos, 200
