"""Pruebas del clasificador de intrusiones (confidencialidad, ASR1).

Usan SQLite en memoria — no requieren PostgreSQL ni el broker. Cubren las dos
señales de sospecha (BOLA y contexto anómalo) y la ventana de correlación.
"""
from datetime import datetime, timezone, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from logica.modelos import Base, HistorialConexion
from logica.clasificador_intrusiones import (
    _sesion_es_sospechosa,
    buscar_sesion_sospechosa,
)


@pytest.fixture()
def session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    s = sessionmaker(bind=engine)()
    yield s
    s.close()


def _sesion(**kw):
    base = dict(
        customer_id_token="CLI-0002",
        customer_id_solicitado="CLI-0001",
        validado=True,
        ip="1.2.3.4",
        device="chrome",
        pais="CO",
        reportado_en=datetime.now(timezone.utc),
    )
    base.update(kw)
    return HistorialConexion(**base)


def test_bola_es_sospechosa():
    # token de un cliente usado para pedir el perfil de otro
    assert "BOLA" in _sesion_es_sospechosa(_sesion())


def test_pais_anomalo_es_sospechosa():
    # mismo customer_id en token y solicitud (sin mismatch) pero país bloqueado
    s = _sesion(customer_id_token="CLI-0001", pais="IR")
    assert "país" in _sesion_es_sospechosa(s)


def test_device_anomalo_es_sospechosa():
    s = _sesion(customer_id_token="CLI-0001", device="unknown-device")
    assert "device" in _sesion_es_sospechosa(s)


def test_sesion_legitima_no_es_sospechosa():
    s = _sesion(customer_id_token="CLI-0001", pais="CO", device="chrome")
    assert _sesion_es_sospechosa(s) is None


def test_rechazo_no_es_sospechosa():
    # una validación rechazada no es una extracción consumada
    s = _sesion(validado=False)
    assert _sesion_es_sospechosa(s) is None


def test_buscar_correlaciona_dentro_de_ventana(session):
    ref = datetime.now(timezone.utc)
    session.add(_sesion(reportado_en=ref))
    session.commit()
    encontrada, motivo = buscar_sesion_sospechosa(session, "CLI-0001", ref)
    assert encontrada is not None and "BOLA" in motivo


def test_buscar_ignora_fuera_de_ventana(session):
    ref = datetime.now(timezone.utc)
    vieja = ref - timedelta(seconds=3600)
    session.add(_sesion(reportado_en=vieja))
    session.commit()
    encontrada, _ = buscar_sesion_sospechosa(session, "CLI-0001", ref)
    assert encontrada is None
