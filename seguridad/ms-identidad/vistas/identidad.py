"""Endpoint ValidarUsuario — lo llama ms-cliente antes de pedir un perfil
de riesgo a ms-riesgo.
"""
from flask_restful import Resource, reqparse

from logica.validar_usuario import TokenInvalido, validar_usuario
from tareas.publicacion import publicar_reporte_sesion

parser = reqparse.RequestParser()
parser.add_argument("token", type=str, required=True, location="json")
parser.add_argument(
    "customer_id_solicitado", type=str, required=True, location="json"
)
parser.add_argument("ip", type=str, required=False, location="json")
parser.add_argument("device", type=str, required=False, location="json")
parser.add_argument("pais", type=str, required=False, location="json")


class ValidarUsuarioRecurso(Resource):
    def post(self):
        args = parser.parse_args()

        try:
            resultado = validar_usuario(
                args["token"], args["customer_id_solicitado"]
            )
        except TokenInvalido as exc:
            publicar_reporte_sesion(
                customer_id_token=None,
                customer_id_solicitado=args["customer_id_solicitado"],
                validado=False,
                ip=args.get("ip"),
                device=args.get("device"),
                pais=args.get("pais"),
            )
            return {"validado": False, "error": str(exc)}, 401

        publicar_reporte_sesion(
            customer_id_token=resultado["customer_id_token"],
            customer_id_solicitado=resultado["customer_id_solicitado"],
            validado=True,
            ip=args.get("ip"),
            device=args.get("device"),
            pais=args.get("pais"),
        )

        return {
            "validado": True,
            "customer_id_token": resultado["customer_id_token"],
        }, 200
