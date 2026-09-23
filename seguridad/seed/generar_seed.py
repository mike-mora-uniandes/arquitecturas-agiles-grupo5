"""Puebla con datos dummy las bases PostgreSQL del experimento de seguridad.

La semilla es reproducible: se puede alternar entre dos escenarios
configurados por variables de entorno:

- baseline: tráfico mayoritariamente legítimo
- attack: mezcla de tráfico legítimo + sospechoso para medir ASR1/ASR2

Esto permite comparar el comportamiento del mismo flujo con dos perfiles de
carga distintos sin depender del azar.
"""
import os
import random
import time
from datetime import datetime, timezone

import psycopg2
from faker import Faker

IDENTIDAD_DB_URL = os.environ["IDENTIDAD_DATABASE_URL"]
RIESGO_DB_URL = os.environ["RIESGO_DATABASE_URL"]

N_CLIENTES = int(os.getenv("SEED_N_CLIENTES", "10"))
SEED_SCENARIO = os.getenv("SEED_SCENARIO", "baseline").lower()
SEED_SEMILLA = int(os.getenv("SEED_SEED", "20240601"))
SEED_ATTACK_RATIO = float(os.getenv("SEED_ATTACK_RATIO", "0.20"))

random.seed(SEED_SEMILLA)
fake = Faker("es_CO")
fake.seed_instance(SEED_SEMILLA)

VICTIMA_CUSTOMER_ID = "CLI-0001"
ANALISTA_CUSTOMER_ID = "ANL-0001"
ROLES = ["cliente_final", "analista_riesgo"]

SCENARIOS = {
    "baseline": {
        "attack_ratio": 0.05,
        "victim_ids": [VICTIMA_CUSTOMER_ID],
        "suspicious_ids": [],
    },
    "attack": {
        "attack_ratio": SEED_ATTACK_RATIO,
        "victim_ids": [VICTIMA_CUSTOMER_ID],
        "suspicious_ids": ["CLI-0002", "CLI-0003", "CLI-0004"],
    },
}


def _scenario_config():
    return SCENARIOS.get(SEED_SCENARIO, SCENARIOS["baseline"])


def _conectar(url, intentos=15, espera_s=2):
    """Postgres puede tardar unos segundos en aceptar conexiones tras
    arrancar — depends_on solo espera a que el contenedor inicie, no a que
    el servidor esté listo.
    """
    for intento in range(1, intentos + 1):
        try:
            return psycopg2.connect(url)
        except psycopg2.OperationalError:
            if intento == intentos:
                raise
            print(f"seed: Postgres no listo aún, reintentando ({intento}/{intentos})...")
            time.sleep(espera_s)


def _cliente_ids():
    return [f"CLI-{indice:04d}" for indice in range(1, N_CLIENTES + 1)]


def _categoria_para_score(score: int) -> str:
    if score >= 66:
        return "ALTO"
    if score >= 34:
        return "MEDIO"
    return "BAJO"


def _is_suspicious(customer_id: str) -> bool:
    return customer_id in _scenario_config()["suspicious_ids"]


def _pais_y_device(customer_id: str):
    if _is_suspicious(customer_id):
        return ("AR", f"device-{customer_id.lower()}-sospechoso")
    return (
        fake.country_code(representation="alpha-2"),
        f"device-{customer_id.lower()}",
    )


def poblar_gestion_roles():
    """Inserta un analista fijo y clientes finales con un patrón
    reproducible para escenario normal o atacante.
    """
    conn = _conectar(IDENTIDAD_DB_URL)
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS roles (
                    nombre TEXT PRIMARY KEY
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS usuarios (
                    customer_id TEXT PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    rol TEXT NOT NULL REFERENCES roles(nombre),
                    pais_habitual TEXT NOT NULL,
                    device_habitual TEXT NOT NULL
                )
                """
            )
            # Auto-reparación: si ms-identidad ganó la carrera de arranque y
            # creó `usuarios` con su propio modelo (customer_id/nombre/rol, sin
            # pais_habitual/device_habitual), el CREATE de arriba es no-op y el
            # INSERT de abajo fallaría por columnas inexistentes. Estas dos
            # sentencias garantizan que las columnas existan gane quien gane la
            # carrera. Son nullable a propósito: ms-identidad no las conoce y no
            # las escribe, pero el seed sí las puebla en el mismo INSERT.
            cur.execute(
                "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS pais_habitual TEXT"
            )
            cur.execute(
                "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS device_habitual TEXT"
            )
            cur.executemany(
                "INSERT INTO roles (nombre) VALUES (%s) ON CONFLICT DO NOTHING",
                [("cliente_final",), ("analista_riesgo",)],
            )

            usuarios = [
                (
                    ANALISTA_CUSTOMER_ID,
                    fake.name(),
                    "analista_riesgo",
                    "CO",
                    "analista-console",
                )
            ]
            for customer_id in _cliente_ids():
                pais_habitual, device_habitual = _pais_y_device(customer_id)
                usuarios.append(
                    (
                        customer_id,
                        fake.name(),
                        "cliente_final",
                        pais_habitual,
                        device_habitual,
                    )
                )

            cur.executemany(
                """
                INSERT INTO usuarios (
                    customer_id, nombre, rol, pais_habitual, device_habitual
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (customer_id) DO NOTHING
                """,
                usuarios,
            )
    finally:
        conn.close()


def poblar_perfil_riesgo():
    """Genera perfiles con un patrón reproducible: en baseline todos son
    legítimos; en attack, se marcan clientes sospechosos con puntajes más
    altos y categorías más riesgo para emular un lote con más ataques.
    """
    conn = _conectar(RIESGO_DB_URL)
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS perfiles_riesgo (
                    customer_id TEXT PRIMARY KEY,
                    nombre_completo TEXT NOT NULL,
                    documento_identidad TEXT NOT NULL,
                    puntaje INTEGER NOT NULL,
                    categoria TEXT NOT NULL,
                    actualizado_en TIMESTAMP NOT NULL
                )
                """
            )

            perfiles = []
            for customer_id in [VICTIMA_CUSTOMER_ID, *[c for c in _cliente_ids() if c != VICTIMA_CUSTOMER_ID]]:
                if SEED_SCENARIO == "attack" and _is_suspicious(customer_id):
                    score = random.randint(70, 95)
                else:
                    score = random.randint(20, 80)
                perfiles.append(
                    (
                        customer_id,
                        fake.name(),
                        str(fake.random_number(digits=8, fix_len=True)),
                        score,
                        _categoria_para_score(score),
                        datetime.now(timezone.utc),
                    )
                )

            cur.executemany(
                """
                INSERT INTO perfiles_riesgo (
                    customer_id, nombre_completo, documento_identidad,
                    puntaje, categoria, actualizado_en
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (customer_id) DO NOTHING
                """,
                perfiles,
            )
    finally:
        conn.close()


if __name__ == "__main__":
    poblar_gestion_roles()
    poblar_perfil_riesgo()
    print(
        f"seed: escenario={SEED_SCENARIO} ratio_ataques={_scenario_config()['attack_ratio']} "
        f"clientes={len(_cliente_ids())}"
    )
