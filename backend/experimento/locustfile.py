"""Matriz de escenarios para el experimento ASR.

Cada escenario usa el mismo customer_id en Open Data y Open Finance para
simular al mismo usuario en ambas fuentes. Esto permite cubrir: línea base,
fallos de timeout, reintentos, fallback por caché y payload anómalo.

Los pesos pueden variarse por variables de entorno para dar más o menos carga a
cada escenario sin tocar el código antes de cada prueba.
"""
import os
import random

from locust import HttpUser, between, task

BASE_URL = "http://wiremock:8080"
DEFAULT_WEIGHTS = {
    "E0": int(os.getenv("E0_WEIGHT", "40")),
    "E1": int(os.getenv("E1_WEIGHT", "18")),
    "E2": int(os.getenv("E2_WEIGHT", "15")),
    "E3": int(os.getenv("E3_WEIGHT", "15")),
    "E4": int(os.getenv("E4_WEIGHT", "8")),
    "E5": int(os.getenv("E5_WEIGHT", "4")),
}

SCENARIO_PLAN = {
    "E0": {
        "customer_id": "C001",
        "open_data": f"{BASE_URL}/open-data/customers/C001",
        "open_finance": f"{BASE_URL}/open-finance/customers/C001",
        "expected_asrs": ["baseline"],
        "description": "Línea base: ambas fuentes OK.",
    },
    "E1": {
        "customer_id": "C002",
        "open_data": f"{BASE_URL}/open-data/customers/C002",
        "open_finance": f"{BASE_URL}/open-finance/customers/C002",
        "expected_asrs": ["ASR1", "ASR3"],
        "description": "Fallo transitorio con timeout inicial y recuperación.",
    },
    "E2": {
        "customer_id": "C003",
        "open_data": f"{BASE_URL}/open-data/customers/C003",
        "open_finance": f"{BASE_URL}/open-finance/customers/C003",
        "expected_asrs": ["ASR1", "ASR3", "ASR2"],
        "description": "Open Data + Open Finance responden 503, fallback degradado.",
    },
    "E3": {
        "customer_id": "C004",
        "open_data": f"{BASE_URL}/open-data/customers/C004",
        "open_finance": f"{BASE_URL}/open-finance/customers/C004",
        "expected_asrs": ["ASR1", "ASR3", "ASR2"],
        "description": "Falla persistente simultánea en ambas fuentes.",
    },
    "E4": {
        "customer_id": "C005",
        "open_data": f"{BASE_URL}/open-data/customers/C005",
        "open_finance": f"{BASE_URL}/open-finance/customers/C005",
        "expected_asrs": ["ASR1"],
        "description": "Payload anómalo: contrato inválido en una fuente.",
    },
    "E5": {
        "customer_id": "C006",
        "open_data": f"{BASE_URL}/open-data/customers/C006",
        "open_finance": f"{BASE_URL}/open-finance/customers/C006",
        "expected_asrs": ["ASR1", "ASR2"],
        "description": "Caché de respaldo y fallo explícito en una o ambas fuentes.",
    },
}

SCENARIO_KEYS = list(SCENARIO_PLAN.keys())
SCENARIO_WEIGHTS = [DEFAULT_WEIGHTS[name] for name in SCENARIO_KEYS]


def pick_scenario():
    return random.choices(SCENARIO_KEYS, weights=SCENARIO_WEIGHTS, k=1)[0]


class AnalystUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def request_evaluation(self):
        scenario_name = pick_scenario()
        scenario = SCENARIO_PLAN[scenario_name]
        customer_id = scenario["customer_id"]

        self.client.post(
            "/evaluations",
            json={
                "customer_id": customer_id,
                "requested_by": "locust",
                "scenario": scenario_name,
            },
            name=f"/evaluations/{scenario_name}",
        )
