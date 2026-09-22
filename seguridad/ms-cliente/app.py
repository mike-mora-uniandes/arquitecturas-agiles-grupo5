"""Punto de entrada HTTP de MS Cliente (andamiaje).

Sin endpoints por ahora. Responsabilidad final: ser el punto de entrada del
flujo (`IConsultarPerfilRiesgoService`), condicionar la entrega del perfil de
riesgo a la validación del usuario (MS Identidad) y a la verificación de
integridad del dato recibido (MS Riesgo, vía ValidadorIntegridad).
"""
from flask import Flask

from config import Config


def crear_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    return app


app = crear_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
