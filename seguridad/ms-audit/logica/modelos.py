"""Modelo de datos de MS Audit (PostgreSQL).

Persistir los eventos es lo que hace posible la correlación de patrones de
intrusión (Vista de Información del diseño): sin un registro durable de
sesiones y extracciones, ms-audit no tendría con qué cruzar ambos lados del
ataque de confidencialidad.

Tres tablas:
- HistorialConexion       ← ReporteSesionAccion (ms-identidad)
- HistorialRegistrosUsuario ← ReporteExtraccionPerfilRiesgoCliente (ms-riesgo)
- Incidente               → lo que ms-audit clasifica como intrusión y notifica
"""
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


class HistorialConexion(Base):
    """Cada intento de ValidarUsuario que reporta ms-identidad (exitoso o
    rechazado). Lleva ambos customer_id para poder detectar el BOLA, y el
    contexto (ip/device/país) para detectar un origen anómalo.
    """

    __tablename__ = "historial_conexion"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id_token = Column(String, nullable=True)
    customer_id_solicitado = Column(String, nullable=False, index=True)
    validado = Column(Boolean, nullable=False)
    ip = Column(String, nullable=True)
    device = Column(String, nullable=True)
    pais = Column(String, nullable=True)
    reportado_en = Column(DateTime(timezone=True), nullable=False)
    registrado_en = Column(DateTime(timezone=True), nullable=False, default=_ahora)


class HistorialRegistrosUsuario(Base):
    """Cada extracción de perfil de riesgo atendida que reporta ms-riesgo.
    `incidentado` evita generar dos veces el mismo incidente por una misma
    extracción cuando la sesión correlacionada llega después.
    """

    __tablename__ = "historial_registros_usuario"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String, nullable=False, index=True)
    reportado_en = Column(DateTime(timezone=True), nullable=False)
    registrado_en = Column(DateTime(timezone=True), nullable=False, default=_ahora)
    incidentado = Column(Boolean, nullable=False, default=False)


class ComportamientoHabitual(Base):
    """Línea base del comportamiento normal de cada cliente (país/device
    habitual). Es dato de referencia sembrado por seed/ (no un evento de
    runtime), y lo usa el clasificador para marcar como anómala una sesión
    cuyo país/device difiere del habitual del actor (Detect Intrusion por
    comportamiento). Puede no existir para un actor desconocido: en ese caso
    no hay señal de comportamiento (se cae a BOLA).
    """

    __tablename__ = "comportamiento_habitual"

    customer_id = Column(String, primary_key=True)
    pais_habitual = Column(String, nullable=True)
    device_habitual = Column(String, nullable=True)


class Incidente(Base):
    """Un patrón clasificado como intrusión no autorizada. `deteccion_ms` es
    la latencia de detección medida (t_detección - t_materialización) que
    alimenta la métrica del ASR correspondiente.
    """

    __tablename__ = "incidentes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tipo = Column(String, nullable=False)  # "confidencialidad" | "integridad"
    customer_id = Column(String, nullable=False, index=True)
    deteccion_ms = Column(Float, nullable=False)
    detalle = Column(String, nullable=True)
    detectado_en = Column(DateTime(timezone=True), nullable=False, default=_ahora)

    def to_dict(self) -> dict:
        return {
            "incidente_id": self.id,
            "tipo": self.tipo,
            "customer_id": self.customer_id,
            "deteccion_ms": self.deteccion_ms,
            "detalle": self.detalle,
            "detectado_en": self.detectado_en.isoformat(),
        }
