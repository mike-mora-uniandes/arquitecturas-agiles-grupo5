"""Pruebas de GeneradorIntegridad: hash determinista y sensible a cualquier
cambio en el payload (para que ValidadorIntegridad, en ms-cliente, pueda
detectar una alteración en tránsito).
"""
from logica.generador_integridad import generar_hash

PERFIL = {
    "customer_id": "CLI-0007",
    "nombre_completo": "Juana Pérez",
    "documento_identidad": "123456",
    "puntaje": 80,
    "categoria": "ALTO",
    "actualizado_en": "2026-01-01T00:00:00+00:00",
}


def test_generar_hash_es_determinista():
    assert generar_hash(PERFIL) == generar_hash(dict(PERFIL))


def test_generar_hash_no_depende_del_orden_de_las_llaves():
    invertido = dict(reversed(list(PERFIL.items())))
    assert generar_hash(PERFIL) == generar_hash(invertido)


def test_generar_hash_cambia_si_se_altera_un_campo():
    alterado = {**PERFIL, "puntaje": 999}
    assert generar_hash(PERFIL) != generar_hash(alterado)
