"""Pruebas del clasificador de intrusiones (confidencialidad, ASR1).

Usan SQLite en memoria — no requieren PostgreSQL ni el broker. Cubren las dos
señales de sospecha (BOLA y comportamiento anómalo vs. habitual) y la ventana
de correlación.
"""
from datetime import datetime, timezone, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from logica.modelos import Base, ComportamientoHabitual, HistorialConexion
from logica.clasificador_intrusiones import (
    _sesion_es_sospechosa,
    buscar_sesion_sospechosa,
)

# Habitual sembrado del actor CLI-0002 (huella normal = CO/desktop-linux).
BASE_HABITUAL = ComportamientoHabitual(
    customer_id="CLI-0002", pais_habitual="CO", device_habitual="desktop-linux"
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
        customer_id_solicitado="CLI-0002",  # sin BOLA por defecto
        validado=True,
        ip="10.0.0.5",
        device="desktop-linux",
        pais="CO",
        reportado_en=datetime.now(timezone.utc),
    )
    base.update(kw)
    return HistorialConexion(**base)


def test_bola_es_sospechosa_sin_baseline():
    # token de un cliente usado para pedir el perfil de otro: dispara sin
    # necesidad de línea base de comportamiento.
    s = _sesion(customer_id_solicitado="CLI-0001")
    assert "BOLA" in _sesion_es_sospechosa(s, None)


def test_pais_distinto_del_habitual_es_sospechosa():
    # mismo customer_id (sin BOLA) pero país distinto al habitual del actor
    s = _sesion(pais="US")
    assert "país" in _sesion_es_sospechosa(s, BASE_HABITUAL)


def test_device_distinto_del_habitual_es_sospechosa():
    s = _sesion(device="device-nuevo")
    assert "device" in _sesion_es_sospechosa(s, BASE_HABITUAL)


def test_sesion_legitima_coincide_con_habitual_no_es_sospechosa():
    s = _sesion(pais="CO", device="desktop-linux")
    assert _sesion_es_sospechosa(s, BASE_HABITUAL) is None


def test_sin_baseline_y_sin_bola_no_es_sospechosa():
    # actor desconocido (sin habitual sembrado) y sin BOLA: no hay señal
    s = _sesion(pais="US", device="lo-que-sea")
    assert _sesion_es_sospechosa(s, None) is None


def test_rechazo_no_es_sospechosa():
    s = _sesion(validado=False, pais="US")
    assert _sesion_es_sospechosa(s, BASE_HABITUAL) is None


def test_buscar_correlaciona_comportamiento_anomalo(session):
    session.add(BASE_HABITUAL)
    ref = datetime.now(timezone.utc)
    # acceso de CLI-0002 a su propio perfil pero desde US (anómalo)
    session.add(_sesion(pais="US", reportado_en=ref))
    session.commit()
    encontrada, motivo = buscar_sesion_sospechosa(session, "CLI-0002", ref)
    assert encontrada is not None and "país" in motivo


def test_buscar_ignora_fuera_de_ventana(session):
    session.add(BASE_HABITUAL)
    ref = datetime.now(timezone.utc)
    vieja = ref - timedelta(seconds=3600)
    session.add(_sesion(customer_id_solicitado="CLI-0001", reportado_en=vieja))
    session.commit()
    encontrada, _ = buscar_sesion_sospechosa(session, "CLI-0001", ref)
    assert encontrada is None
