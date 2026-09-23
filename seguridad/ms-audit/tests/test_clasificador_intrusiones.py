"""Pruebas del detector heurístico de intrusiones (confidencialidad, ASR1).

SQLite en memoria — sin PostgreSQL ni broker. Cubren: BOLA, comportamiento
probabilístico (país/device improbable vs. historial del actor), patrones
múltiples legítimos, exclusión de conexiones anómalas (anti-envenenamiento),
historial insuficiente y el emparejamiento por request_id.
"""
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from logica.detector import evaluar
from logica.clasificador_intrusiones import evaluar_request
from logica.modelos import Base, HistorialConexion


@pytest.fixture()
def session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    s = sessionmaker(bind=engine)()
    yield s
    s.close()


def _conexion(**kw):
    base = dict(
        request_id=None,
        customer_id_token="CLI-0002",
        customer_id_solicitado="CLI-0002",
        validado=True,
        ip="10.0.0.5",
        device="desktop-linux",
        pais="CO",
        reportado_en=datetime.now(timezone.utc),
        anomala=False,
    )
    base.update(kw)
    return HistorialConexion(**base)


def _historial_normal(session, actor="CLI-0002", n=5, pais="CO", device="desktop-linux",
                      anomala=False):
    for _ in range(n):
        session.add(_conexion(customer_id_token=actor, customer_id_solicitado=actor,
                              pais=pais, device=device, anomala=anomala))
    session.commit()


def test_bola_es_intrusion_sin_historial(session):
    s = _conexion(customer_id_token="CLI-0002", customer_id_solicitado="CLI-0001")
    session.add(s); session.commit()
    es, score, motivos = evaluar(session, s)
    assert es and score == 1.0 and "BOLA" in motivos[0]


def test_comportamiento_pais_improbable_es_intrusion(session):
    _historial_normal(session, n=5, pais="CO", device="desktop-linux")
    s = _conexion(pais="US", device="device-nuevo")
    session.add(s); session.commit()
    es, score, motivos = evaluar(session, s)
    assert es and "anómalo" in motivos[0]


def test_comportamiento_habitual_no_es_intrusion(session):
    _historial_normal(session, n=5, pais="CO", device="desktop-linux")
    s = _conexion(pais="CO", device="desktop-linux")
    session.add(s); session.commit()
    es, _score, _m = evaluar(session, s)
    assert es is False


def test_patrones_multiples_legitimos_no_marca(session):
    # el actor usa CO y US legítimamente -> una request desde US no es anómala
    _historial_normal(session, n=5, pais="CO", device="desktop-linux")
    _historial_normal(session, n=5, pais="US", device="desktop-linux")
    s = _conexion(pais="US", device="desktop-linux")
    session.add(s); session.commit()
    es, _score, _m = evaluar(session, s)
    assert es is False


def test_conexiones_anomalas_no_envenenan(session):
    # 5 normales CO + 5 anómalas US (marcadas): US sigue siendo improbable
    _historial_normal(session, n=5, pais="CO", device="desktop-linux")
    _historial_normal(session, n=5, pais="US", device="device-nuevo", anomala=True)
    s = _conexion(pais="US", device="device-nuevo")
    session.add(s); session.commit()
    es, _score, motivos = evaluar(session, s)
    assert es and "anómalo" in motivos[0]


def test_historial_insuficiente_solo_bola(session):
    # con 1 sola conexión previa (< min muestras) no hay señal de comportamiento
    _historial_normal(session, n=1, pais="CO", device="desktop-linux")
    s = _conexion(pais="US", device="device-nuevo")
    session.add(s); session.commit()
    es, _score, _m = evaluar(session, s)
    assert es is False


def test_evaluar_request_empareja_por_id(session):
    _historial_normal(session, n=5, pais="CO", device="desktop-linux")
    session.add(_conexion(request_id="req-A", pais="US", device="device-nuevo"))
    session.commit()
    sesion, motivo = evaluar_request(session, "req-A")
    assert sesion is not None and "anómalo" in motivo


def test_evaluar_request_sin_sesion(session):
    assert evaluar_request(session, "req-inexistente") == (None, None)
