"""Pruebas del clasificador de intrusiones (confidencialidad, ASR1).

Usan SQLite en memoria — no requieren PostgreSQL ni el broker. Cubren las dos
señales de sospecha (BOLA y comportamiento anómalo vs. habitual) y el
emparejamiento exacto sesión↔extracción por request_id.
"""
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from logica.modelos import Base, ComportamientoHabitual, HistorialConexion
from logica.clasificador_intrusiones import _sesion_es_sospechosa, evaluar_request

# Habitual del actor CLI-0002 (huella normal = CO/desktop-linux). Para las
# aserciones puras (_sesion_es_sospechosa) basta un objeto suelto; para las
# pruebas con BD se usa _habitual() (instancia nueva por sesión, no se puede
# reutilizar la misma entre sesiones SQLite distintas).
BASE_HABITUAL = ComportamientoHabitual(
    customer_id="CLI-0002", pais_habitual="CO", device_habitual="desktop-linux"
)


def _habitual():
    return ComportamientoHabitual(
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
        request_id="req-1",
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


# --- señal pura (_sesion_es_sospechosa) ---

def test_bola_es_sospechosa_sin_baseline():
    s = _sesion(customer_id_solicitado="CLI-0001")
    assert "BOLA" in _sesion_es_sospechosa(s, None)


def test_pais_distinto_del_habitual_es_sospechosa():
    assert "país" in _sesion_es_sospechosa(_sesion(pais="US"), BASE_HABITUAL)


def test_device_distinto_del_habitual_es_sospechosa():
    assert "device" in _sesion_es_sospechosa(_sesion(device="device-nuevo"), BASE_HABITUAL)


def test_sesion_legitima_coincide_con_habitual_no_es_sospechosa():
    assert _sesion_es_sospechosa(_sesion(), BASE_HABITUAL) is None


def test_sin_baseline_y_sin_bola_no_es_sospechosa():
    assert _sesion_es_sospechosa(_sesion(pais="US"), None) is None


def test_rechazo_no_es_sospechosa():
    assert _sesion_es_sospechosa(_sesion(validado=False, pais="US"), BASE_HABITUAL) is None


# --- emparejamiento por request_id (evaluar_request) ---

def test_evaluar_request_anomalo(session):
    session.add(_habitual())
    session.add(_sesion(request_id="req-A", pais="US"))
    session.commit()
    assert "país" in evaluar_request(session, "req-A")


def test_evaluar_request_legitimo(session):
    session.add(_habitual())
    session.add(_sesion(request_id="req-B"))  # CO/desktop-linux = habitual
    session.commit()
    assert evaluar_request(session, "req-B") is None


def test_evaluar_request_sin_sesion_todavia(session):
    # la extracción llegó antes que su sesión: aún no se puede clasificar
    assert evaluar_request(session, "req-inexistente") is None


def test_cada_request_se_evalua_independiente(session):
    # misma cuenta, dos requests distintas: una legítima y una anómala.
    session.add(_habitual())
    session.add(_sesion(request_id="req-legit", pais="CO", device="desktop-linux"))
    session.add(_sesion(request_id="req-mal", pais="US", device="device-nuevo"))
    session.commit()
    assert evaluar_request(session, "req-legit") is None
    assert "país" in evaluar_request(session, "req-mal")
