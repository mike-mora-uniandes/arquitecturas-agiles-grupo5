"""Modelo de persistencia de MS PerfilRiesgo (esqueleto)."""
from extensiones import db


class PerfilRiesgo(db.Model):
    __tablename__ = "perfil_riesgo"

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.String(64), index=True, nullable=False)
    # TODO: campos del perfil calculado (score, categoría, fuentes, fecha...).
