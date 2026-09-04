import pytest
import responses

from logica import fuentes_externas as fx
from logica.deteccion_excepciones import FalloReintentable, RespuestaAnomala


def _body(system, cid, valor=42):
    campo = "data_risk" if system == "open_data" else "financial_risk"
    return {"customer_id": cid, campo: valor}


@responses.activate
def test_respuesta_valida():
    responses.get(fx.url_de("open_data", "C1"), json=_body("open_data", "C1"), status=200)
    assert fx.consultar("open_data", "C1", 1.0)["data_risk"] == 42


@responses.activate
def test_503_es_reintentable():
    responses.get(fx.url_de("open_finance", "C1"), status=503)
    with pytest.raises(FalloReintentable) as exc:
        fx.consultar("open_finance", "C1", 1.0)
    assert exc.value.clase == "http_5xx"


@responses.activate
def test_4xx_es_anomala():
    responses.get(fx.url_de("open_data", "C1"), status=404)
    with pytest.raises(RespuestaAnomala):
        fx.consultar("open_data", "C1", 1.0)


@responses.activate
def test_esquema_invalido_es_anomala():
    responses.get(
        fx.url_de("open_data", "C1"),
        json={"customer_id": "C1", "data_risk": "N/A", "contract_version": "2.0"},
        status=200,
    )
    with pytest.raises(RespuestaAnomala):
        fx.consultar("open_data", "C1", 1.0)


@responses.activate
def test_customer_id_no_coincide_es_anomala():
    responses.get(
        fx.url_de("open_data", "C1"),
        json={"customer_id": "OTRO", "data_risk": 10}, status=200,
    )
    with pytest.raises(RespuestaAnomala):
        fx.consultar("open_data", "C1", 1.0)
