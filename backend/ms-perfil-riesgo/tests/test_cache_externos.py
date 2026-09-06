from logica import cache_externos


def test_miss_devuelve_none(fake_redis):
    assert cache_externos.leer("SIN_DATOS") is None


def test_escribir_y_leer(fake_redis):
    cache_externos.escribir(
        "CX", {"score": 55, "category": "MEDIUM"}, "corr-1",
        {"open_data": "ok", "open_finance": "ok"},
    )
    perfil = cache_externos.leer("CX")
    assert perfil["score"] == 55
    assert perfil["category"] == "MEDIUM"
    assert perfil["snapshot_type"] == "LIVE_EVALUATION"
    assert perfil["model_version"] == "v1"
    assert fake_redis.ttl("profile:CX") > 0
