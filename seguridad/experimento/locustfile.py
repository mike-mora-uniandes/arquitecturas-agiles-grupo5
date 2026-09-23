"""Carga concurrente para el experimento de seguridad.

Dos perfiles reproducibles:

- baseline: mayoritariamente tráfico legítimo, pocos casos sospechosos
- attack: mezcla de tráfico legítimo + sospechoso para comparar tendencia y
  latencia bajo presión

Se configura con variables de entorno del proyecto:
    SCENARIO=baseline|attack
    SECURITY_BASE_URL=http://localhost:6002
    JWT_SECRET=change-me
    LOAD_SEED=20240601

Ejemplo de ejecución:
    $env:SCENARIO='baseline'; locust -f seguridad/experimento/locustfile.py --host http://localhost:6002
    $env:SCENARIO='attack'; locust -f seguridad/experimento/locustfile.py --host http://localhost:6002
"""
import os
import random
from datetime import datetime, timedelta, timezone

import jwt
from locust import HttpUser, between, task

BASE_URL = os.getenv("SECURITY_BASE_URL", "http://localhost:6002")
##SCENARIO = os.getenv("SCENARIO", "baseline").lower()
SCENARIO = os.getenv("SCENARIO", "attack").lower()
JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
LOAD_SEED = int(os.getenv("LOAD_SEED", "20240601"))

CUSTOMERS = [f"CLI-{index:04d}" for index in range(1, 11)]
CUSTOMERS_VALID = ["CLI-0001", "CLI-0002", "CLI-0003", "CLI-0004", "CLI-0005"]

SCENARIO_CONFIG = {
    "baseline": {
        "legit": 95,
        "unauthorized": 2,
        "anomaly_ip": 2,
        "expired": 0,
        "invalid_sig": 1,
    },
    "attack": {
        "legit": 70,
        "unauthorized": 15,
        "anomaly_ip": 10,
        "expired": 3,
        "invalid_sig": 2,
    },
}

RAND = random.Random(LOAD_SEED)


def _make_jwt(customer_id: str, *, expires_in_seconds: int = 300, secret: str = JWT_SECRET):
    now = datetime.now(timezone.utc)
    payload = {
        "customer_id": customer_id,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=expires_in_seconds)).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def _make_expired_jwt(customer_id: str):
    now = datetime.now(timezone.utc)
    payload = {
        "customer_id": customer_id,
        "iat": int((now - timedelta(minutes=10)).timestamp()),
        "nbf": int((now - timedelta(minutes=10)).timestamp()),
        "exp": int((now - timedelta(minutes=1)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def _make_invalid_jwt(customer_id: str):
    return _make_jwt(customer_id, secret="invalid-secret")


def _pick_case():
    config = SCENARIO_CONFIG.get(SCENARIO, SCENARIO_CONFIG["baseline"])
    items = []
    for name, weight in config.items():
        items.extend([name] * weight)
    return RAND.choice(items)


class SeguridadUser(HttpUser):
    wait_time = between(0.5, 2.0)
    host = BASE_URL

    @task(1)
    def perfil_riesgo(self):
        case = _pick_case()
        actor_id = RAND.choice(CUSTOMERS_VALID)
        target_id = RAND.choice(CUSTOMERS)

        if case == "legit":
            customer_id = actor_id
            token = _make_jwt(customer_id)
            body = {
                "token": token,
                "customer_id": customer_id,
                "ip": "10.0.0.5",
                "device": "desktop-linux",
                "pais": "CO",
            }
            name = "/perfil-riesgo/legit"
        elif case == "unauthorized":
            customer_id = target_id
            token = _make_jwt(actor_id)
            body = {
                "token": token,
                "customer_id": customer_id,
                "ip": "203.0.113.10",
                "device": "android-suspicious",
                "pais": "AR",
            }
            name = "/perfil-riesgo/unauthorized"
        elif case == "anomaly_ip":
            customer_id = actor_id
            token = _make_jwt(customer_id)
            body = {
                "token": token,
                "customer_id": customer_id,
                "ip": "198.51.100.9",
                "device": "device-nuevo",
                "pais": "US",
            }
            name = "/perfil-riesgo/anomaly-ip"
        elif case == "expired":
            customer_id = actor_id
            body = {
                "token": _make_expired_jwt(customer_id),
                "customer_id": customer_id,
                "ip": "10.0.0.5",
                "device": "desktop-linux",
                "pais": "CO",
            }
            name = "/perfil-riesgo/expired"
        elif case == "invalid_sig":
            customer_id = actor_id
            body = {
                "token": _make_invalid_jwt(customer_id),
                "customer_id": customer_id,
                "ip": "10.0.0.5",
                "device": "desktop-linux",
                "pais": "CO",
            }
            name = "/perfil-riesgo/invalid-sig"
        else:
            customer_id = actor_id
            token = _make_jwt(customer_id)
            body = {
                "token": token,
                "customer_id": customer_id,
                "ip": "10.0.0.5",
                "device": "desktop-linux",
                "pais": "CO",
            }
            name = "/perfil-riesgo/fallback"

        self.client.post(
            "/perfil-riesgo",
            json=body,
            name=name,
            timeout=10,
        )
