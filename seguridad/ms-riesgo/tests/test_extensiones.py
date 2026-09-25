"""Pruebas de esperar_bd: Postgres puede tardar en aceptar conexiones tras
arrancar (depends_on solo espera a que el contenedor inicie, no a que el
servidor esté listo) — reintenta hasta `intentos` veces antes de propagar
el error.
"""
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import OperationalError

from extensiones import esperar_bd


def _engine_que_falla(veces_antes_de_conectar):
    llamadas = {"n": 0}

    def connect():
        llamadas["n"] += 1
        if llamadas["n"] <= veces_antes_de_conectar:
            raise OperationalError("conexión rechazada", None, None)
        return MagicMock()  # soporta 'with engine.connect():' por defecto

    engine = MagicMock()
    engine.connect.side_effect = connect
    return engine, llamadas


@patch("extensiones.time.sleep")
def test_esperar_bd_reintenta_hasta_conectar(mock_sleep):
    engine, llamadas = _engine_que_falla(veces_antes_de_conectar=2)

    esperar_bd(engine, intentos=5, espera_s=0)

    assert llamadas["n"] == 3
    assert mock_sleep.call_count == 2


@patch("extensiones.time.sleep")
def test_esperar_bd_propaga_el_error_tras_agotar_intentos(mock_sleep):
    engine, _ = _engine_que_falla(veces_antes_de_conectar=999)

    with pytest.raises(OperationalError):
        esperar_bd(engine, intentos=3, espera_s=0)

    assert mock_sleep.call_count == 2  # no duerme después del último intento
