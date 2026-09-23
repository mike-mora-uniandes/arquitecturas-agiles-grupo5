"""Tareas Celery que consumen los eventos de ms-identidad, ms-riesgo y
ms-cliente, persisten el historial de auditoría, clasifican patrones de
intrusión y publican el incidente + emiten las métricas de detección.

Notas de tiempo (todas las marcas son UTC; el experimento corre en un solo
host con Docker Compose, así que los relojes de los contenedores comparten el
del kernel y las restas entre servicios son comparables — ver README):
- Confidencialidad (ASR1): t0 = momento en que se completó la extracción
  (`reportado_en` del evento de ms-riesgo); t1 = momento en que ms-audit la
  clasifica como intrusión. La resta mide el camino asíncrono
  (publicar → broker → consumir → clasificar), justo el punto de
  incertidumbre del diseño frente al umbral de 200 ms.
- Integridad (ASR2): la latencia la mide ms-cliente inline (verifica el hash)
  y la reporta en `deteccion_ms`; ms-audit solo la centraliza como métrica.
"""
import logging
from datetime import datetime, timezone

import telemetria
from config import Config
from extensiones import Session, celery_app
from logica.clasificador_intrusiones import buscar_sesion_sospechosa
from logica.modelos import (
    HistorialConexion,
    HistorialRegistrosUsuario,
    Incidente,
)
from tareas.publicador import publicar_incidente

log = logging.getLogger(__name__)


def _parse_ts(valor: str) -> datetime:
    """Parsea un ISO-8601 a datetime aware (UTC)."""
    dt = datetime.fromisoformat(valor)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _registrar_incidente(session, *, tipo, customer_id, deteccion_ms, detalle):
    """Crea el incidente, lo persiste, emite las métricas de detección y lo
    publica hacia ms-notificaciones.
    """
    incidente = Incidente(
        tipo=tipo,
        customer_id=customer_id,
        deteccion_ms=deteccion_ms,
        detalle=detalle,
    )
    session.add(incidente)
    session.commit()

    datos = incidente.to_dict()

    telemetria.intrusiones_total.add(1, {"tipo": tipo})
    if tipo == "confidencialidad":
        telemetria.deteccion_confidencialidad_ms.record(deteccion_ms)
        dentro = deteccion_ms <= Config.ASR1_UMBRAL_MS
        telemetria.asr1_within_threshold_total.add(1, {"pass": str(dentro).lower()})
    else:  # integridad
        telemetria.deteccion_integridad_ms.record(deteccion_ms)
        dentro = deteccion_ms <= Config.ASR2_UMBRAL_MS
        telemetria.asr2_within_threshold_total.add(1, {"pass": str(dentro).lower()})

    log.warning(
        "INTRUSION %s customer_id=%s deteccion_ms=%.1f dentro_umbral=%s :: %s",
        tipo, customer_id, deteccion_ms, dentro, detalle,
    )
    publicar_incidente(datos)
    return datos


@celery_app.task(bind=True, name=Config.SESION_ACCION_TASK_NAME)
def registrar_sesion_accion(self, evento):
    """ReporteSesionAccion (ms-identidad) → HistorialConexion. Tras persistir,
    intenta correlacionar con una extracción ya registrada y aún no
    incidentada (la sesión puede llegar después de la extracción).
    """
    log.info("ReporteSesionAccion recibido: %s", evento)
    session = Session()
    try:
        session.add(
            HistorialConexion(
                customer_id_token=evento.get("customer_id_token"),
                customer_id_solicitado=evento["customer_id_solicitado"],
                validado=bool(evento.get("validado")),
                ip=evento.get("ip"),
                device=evento.get("device"),
                pais=evento.get("pais"),
                reportado_en=_parse_ts(evento["reportado_en"]),
            )
        )
        session.commit()
        _correlacionar_confidencialidad(session, evento["customer_id_solicitado"])
    finally:
        Session.remove()


@celery_app.task(bind=True, name=Config.EXTRACCION_TASK_NAME)
def registrar_extraccion_perfil(self, evento):
    """ReporteExtraccionPerfilRiesgoCliente (ms-riesgo) →
    HistorialRegistrosUsuario. Tras persistir, intenta correlacionar con una
    sesión sospechosa.
    """
    log.info("ReporteExtraccionPerfilRiesgoCliente recibido: %s", evento)
    session = Session()
    try:
        session.add(
            HistorialRegistrosUsuario(
                customer_id=evento["customer_id"],
                reportado_en=_parse_ts(evento["reportado_en"]),
            )
        )
        session.commit()
        _correlacionar_confidencialidad(session, evento["customer_id"])
    finally:
        Session.remove()


@celery_app.task(bind=True, name=Config.INTEGRIDAD_TASK_NAME)
def registrar_integridad_fallida(self, evento):
    """IntegridadFallida (ms-cliente) → incidente de integridad directo.

    ms-cliente ya detectó la manipulación (hash que no coincide) y midió la
    latencia inline; ms-audit centraliza la métrica y la notificación.
    Evento esperado: {customer_id, deteccion_ms, detectado_en?, detalle?}.
    """
    log.info("IntegridadFallida recibido: %s", evento)
    session = Session()
    try:
        _registrar_incidente(
            session,
            tipo="integridad",
            customer_id=evento["customer_id"],
            deteccion_ms=float(evento["deteccion_ms"]),
            detalle=evento.get(
                "detalle", "hash de integridad no coincide (manipulación en tránsito)"
            ),
        )
    finally:
        Session.remove()


def _correlacionar_confidencialidad(session, customer_id: str):
    """Busca una extracción no incidentada de `customer_id` que cruce con una
    sesión sospechosa; si la encuentra, levanta el incidente de
    confidencialidad y marca la extracción para no duplicarlo.
    """
    extraccion = session.query(HistorialRegistrosUsuario).filter_by(
        customer_id=customer_id, incidentado=False
    ).order_by(HistorialRegistrosUsuario.reportado_en.desc()).first()
    if extraccion is None:
        return

    sesion, motivo = buscar_sesion_sospechosa(
        session, customer_id, extraccion.reportado_en
    )
    if sesion is None:
        return

    ahora = datetime.now(timezone.utc)
    deteccion_ms = (ahora - extraccion.reportado_en).total_seconds() * 1000.0

    extraccion.incidentado = True
    session.commit()

    _registrar_incidente(
        session,
        tipo="confidencialidad",
        customer_id=customer_id,
        deteccion_ms=deteccion_ms,
        detalle=motivo,
    )
