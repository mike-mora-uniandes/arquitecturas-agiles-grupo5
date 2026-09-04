"""Script de carga base para el experimento (DESIGN.md §2.5).

Genera solicitudes de evaluación contra el endpoint REST de MS Riesgos, rotando
entre los clientes de prueba C001..C006 (cada uno mapea a un escenario fijo en
Wiremock). No espera el resultado: es asíncrono y las métricas de ASR salen de
Grafana.

Pendiente: ajustar la ruta/campos del POST cuando MS Riesgos exponga su endpoint,
y las fases de carga (baseline / carga / pico).
"""
import random

from locust import HttpUser, between, task

CUSTOMERS = ["C001", "C002", "C003", "C004", "C005", "C006"]
# Mezcla sugerida: 40% C001, 12% cada uno del resto.
WEIGHTS = [40, 12, 12, 12, 12, 12]


class AnalystUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def request_evaluation(self):
        customer_id = random.choices(CUSTOMERS, weights=WEIGHTS, k=1)[0]
        self.client.post(
            "/evaluations",
            json={"customer_id": customer_id, "requested_by": "locust"},
            name="/evaluations",
        )
