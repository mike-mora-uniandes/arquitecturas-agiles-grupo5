"""CalculoPerfil — score y categoría del perfil de riesgo.

Fórmula determinista (el experimento mide disponibilidad, no exactitud).
"""


def calcular(open_data: dict, open_finance: dict) -> dict:
    data_risk = float(open_data["data_risk"])
    financial_risk = float(open_finance["financial_risk"])
    score = round(0.6 * financial_risk + 0.4 * data_risk)
    if score < 34:
        category = "LOW"
    elif score <= 66:
        category = "MEDIUM"
    else:
        category = "HIGH"
    return {"score": score, "category": category}
