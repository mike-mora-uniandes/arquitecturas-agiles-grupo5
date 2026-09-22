"""Modelo de datos de PerfilRiesgo.

Datos dummy (Faker, ver ../../seed/) — es el dato sensible (PII) que
custodia el servicio y el objetivo del ataque de confidencialidad (ASR1).
Escala de `puntaje`/`categoria` alineada con
`backend/ms-perfil-riesgo/logica/calculo_perfil.py` (0-100, cortes en 34/66)
para mantener el mismo concepto de "perfil de riesgo" entre los dos
experimentos, solo traducida al español.
"""
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class PerfilRiesgo(Base):
    __tablename__ = "perfiles_riesgo"

    customer_id = Column(String, primary_key=True)  # ej. "CLI-0001"
    nombre_completo = Column(String, nullable=False)
    documento_identidad = Column(String, nullable=False)
    puntaje = Column(Integer, nullable=False)  # 0-100
    categoria = Column(String, nullable=False)  # BAJO (<34) / MEDIO (34-66) / ALTO (>66)
    actualizado_en = Column(DateTime, nullable=False)

    def to_dict(self):
        return {
            "customer_id": self.customer_id,
            "nombre_completo": self.nombre_completo,
            "documento_identidad": self.documento_identidad,
            "puntaje": self.puntaje,
            "categoria": self.categoria,
            "actualizado_en": self.actualizado_en.isoformat(),
        }
