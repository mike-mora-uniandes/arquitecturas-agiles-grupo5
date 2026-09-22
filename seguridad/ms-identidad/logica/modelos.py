"""Modelo de datos de GestiónRoles.

Solo lo esencial para el experimento: quién es cada customer_id y qué rol
tiene. No hay login real (usuario/contraseña) — el login/auth es dummy a
propósito, ver ../README.md.
"""
from sqlalchemy import Column, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Usuario(Base):
    __tablename__ = "usuarios"

    customer_id = Column(String, primary_key=True)
    nombre = Column(String, nullable=False)
    rol = Column(String, nullable=False, default="cliente_final")

    def to_dict(self):
        return {
            "customer_id": self.customer_id,
            "nombre": self.nombre,
            "rol": self.rol,
        }
