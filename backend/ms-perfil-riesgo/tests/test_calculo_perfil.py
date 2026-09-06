from logica import calculo_perfil


def test_score_ponderado_y_categoria_low():
    # 0.6*20 + 0.4*10 = 16 -> LOW
    r = calculo_perfil.calcular({"data_risk": 10}, {"financial_risk": 20})
    assert r == {"score": 16, "category": "LOW"}


def test_limites_de_categoria():
    assert calculo_perfil.calcular({"data_risk": 33}, {"financial_risk": 33})["category"] == "LOW"
    assert calculo_perfil.calcular({"data_risk": 50}, {"financial_risk": 50})["category"] == "MEDIUM"
    assert calculo_perfil.calcular({"data_risk": 90}, {"financial_risk": 90})["category"] == "HIGH"
