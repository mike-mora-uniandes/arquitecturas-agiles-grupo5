"""Cliente HTTP hacia Open Data / Open Finance + validación de esquema (§2.3).

El escenario de fallo lo elige Wiremock según el `customer_id` de la ruta.
"""
import requests

from config import Config
from logica.deteccion_excepciones import (
    CONNECTION,
    HTTP_5XX,
    TIMEOUT,
    FalloReintentable,
    RespuestaAnomala,
)

_BASE = {"open_data": Config.OPEN_DATA_URL, "open_finance": Config.OPEN_FINANCE_URL}
_RISK_FIELD = {"open_data": "data_risk", "open_finance": "financial_risk"}


def url_de(system: str, customer_id: str) -> str:
    return f"{_BASE[system]}/customers/{customer_id}"


def consultar(system: str, customer_id: str, timeout_s: float) -> dict:
    """Devuelve el JSON de la fuente o lanza FalloReintentable / RespuestaAnomala."""
    try:
        resp = requests.get(url_de(system, customer_id), timeout=timeout_s)
    except requests.Timeout as exc:
        raise FalloReintentable(TIMEOUT) from exc
    except requests.ConnectionError as exc:
        raise FalloReintentable(CONNECTION) from exc
    except requests.RequestException as exc:
        raise FalloReintentable(CONNECTION) from exc

    if resp.status_code >= 500 or resp.status_code == 429:
        raise FalloReintentable(HTTP_5XX)
    if resp.status_code != 200:
        raise RespuestaAnomala(f"http_{resp.status_code}")

    try:
        data = resp.json()
    except ValueError as exc:
        raise RespuestaAnomala("el cuerpo no es JSON") from exc

    _validar(system, customer_id, data)
    return data


def _validar(system: str, customer_id: str, data) -> None:
    if not isinstance(data, dict):
        raise RespuestaAnomala("el cuerpo no es un objeto")
    if str(data.get("customer_id")) != str(customer_id):
        raise RespuestaAnomala("customer_id no coincide")
    campo = _RISK_FIELD[system]
    valor = data.get(campo)
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise RespuestaAnomala(f"'{campo}' ausente o no numérico")
    if not 0 <= valor <= 100:
        raise RespuestaAnomala(f"'{campo}' fuera de rango 0..100")
