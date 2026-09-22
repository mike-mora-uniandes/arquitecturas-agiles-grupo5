"""Endpoint IConsultarPerfilRiesgoService — punto de entrada del flujo.
Orquesta MS Identidad -> MS Riesgo (logica/orquestador.py) y traduce el
resultado a la respuesta HTTP.
"""
from flask_restful import Resource, reqparse

from logica.orquestador import (
    IntegridadInvalida,
    PerfilNoEncontrado,
    UsuarioNoValidado,
    consultar_perfil_riesgo,
)

parser = reqparse.RequestParser()
parser.add_argument("token", type=str, required=True, location="json")
parser.add_argument("customer_id", type=str, required=True, location="json")
parser.add_argument("ip", type=str, required=False, location="json")
parser.add_argument("device", type=str, required=False, location="json")
parser.add_argument("pais", type=str, required=False, location="json")


class ConsultarPerfilRiesgoRecurso(Resource):
    def post(self):
        args = parser.parse_args()

        try:
            perfil = consultar_perfil_riesgo(
                token=args["token"],
                customer_id_solicitado=args["customer_id"],
                ip=args.get("ip"),
                device=args.get("device"),
                pais=args.get("pais"),
            )
        except UsuarioNoValidado as exc:
            return {"error": exc.detalle}, 401
        except PerfilNoEncontrado:
            return {"error": f"perfil '{args['customer_id']}' no encontrado"}, 404
        except IntegridadInvalida:
            return {
                "error": "el perfil recibido no superó la verificación de integridad"
            }, 502

        return perfil, 200
