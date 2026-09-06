"""Flujo de la tarea `evaluate_profile` con las fuentes externas simuladas."""
import pytest

import tareas.evaluacion as ev
from logica import cache_externos
from logica.consulta_perfil import ResultadoFuente
from mensajes import (
    SOURCE_CACHE,
    SOURCE_LIVE,
    SOURCE_RETRY,
    STATUS_DEGRADED,
    STATUS_DEGRADED_NO_FALLBACK,
    STATUS_OK,
)


@pytest.fixture(autouse=True)
def publicados(monkeypatch):
    out = []
    monkeypatch.setattr(ev, "publicar_resultado", out.append)
    return out


def _req(cid="corr-1", customer="C1"):
    return {"correlation_id": cid, "customer_id": customer, "requested_by": "t"}


def _fuente(system, ok, data=None, attempts=1, det_ms=None):
    return ResultadoFuente(
        system, ok, data, attempts, 0.0,
        None if ok else "timeout", det_ms,
    )


def _stub(monkeypatch, od, ofin):
    monkeypatch.setattr(
        ev, "consultar_perfil", lambda cid: {"open_data": od, "open_finance": ofin}
    )


def _run(req):
    return ev.evaluate_profile.delay(req).get()


def test_ambas_fuentes_ok_source_live(monkeypatch, publicados):
    _stub(monkeypatch,
          _fuente("open_data", True, {"data_risk": 10}),
          _fuente("open_finance", True, {"financial_risk": 20}))
    assert _run(_req()) == STATUS_OK
    assert publicados[-1]["source"] == SOURCE_LIVE
    assert publicados[-1]["profile"]["score"] == 16


def test_con_reintento_source_retry(monkeypatch, publicados):
    _stub(monkeypatch,
          _fuente("open_data", True, {"data_risk": 10}, attempts=2),
          _fuente("open_finance", True, {"financial_risk": 20}))
    _run(_req())
    assert publicados[-1]["source"] == SOURCE_RETRY


def test_fuente_falla_con_respaldo_degraded(monkeypatch, publicados):
    cache_externos.escribir("C1", {"score": 70, "category": "HIGH"}, "seed",
                            {"open_data": "ok", "open_finance": "ok"})
    _stub(monkeypatch,
          _fuente("open_data", False, det_ms=120.0),
          _fuente("open_finance", True, {"financial_risk": 20}))
    assert _run(_req()) == STATUS_DEGRADED
    assert publicados[-1]["source"] == SOURCE_CACHE
    assert publicados[-1]["profile"]["score"] == 70


def test_fuente_falla_sin_respaldo(monkeypatch, publicados):
    _stub(monkeypatch,
          _fuente("open_data", False, det_ms=120.0),
          _fuente("open_finance", False, det_ms=130.0))
    assert _run(_req(customer="C404")) == STATUS_DEGRADED_NO_FALLBACK
    assert publicados[-1]["profile"] is None
    assert publicados[-1]["reason"]


def test_idempotencia_republica_sin_recalcular(monkeypatch, publicados):
    _stub(monkeypatch,
          _fuente("open_data", True, {"data_risk": 10}),
          _fuente("open_finance", True, {"financial_risk": 20}))
    _run(_req(cid="dup"))
    n = len(publicados)

    def _boom(_cid):
        raise AssertionError("no debe recalcular en un duplicado")

    monkeypatch.setattr(ev, "consultar_perfil", _boom)
    assert _run(_req(cid="dup")) == "republished"
    assert len(publicados) == n + 1
    assert publicados[-1]["correlation_id"] == "dup"
