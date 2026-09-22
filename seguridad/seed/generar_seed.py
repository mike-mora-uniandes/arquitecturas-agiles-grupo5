"""Puebla con datos dummy (Faker) las bases PostgreSQL del experimento:
GestiónRoles (ms-identidad) y PerfilRiesgo (ms-riesgo).

Idempotente: pensado para correr cada vez que se levanta el experimento
desde cero (`docker compose up`), igual espíritu que backend/redis/seed en
el experimento 1. Crea sus propias tablas (`CREATE TABLE IF NOT EXISTS`) en
vez de depender del orden de arranque de los microservicios.
"""
import os
import random
import time
from datetime import datetime, timezone

import psycopg2
from faker import Faker

fake = Faker("es_CO")

IDENTIDAD_DB_URL = os.environ["IDENTIDAD_DATABASE_URL"]
RIESGO_DB_URL = os.environ["RIESGO_DATABASE_URL"]

N_CLIENTES = int(os.getenv("SEED_N_CLIENTES", "10"))

VICTIMA_CUSTOMER_ID = "CLI-0001"
ANALISTA_CUSTOMER_ID = "ANL-0001"
ROLES = ["cliente_final", "analista_riesgo"]


def _conectar(url, intentos=15, espera_s=2):
    """Postgres puede tardar unos segundos en aceptar conexiones tras
    arrancar — depends_on solo espera a que el contenedor inicie, no a que
    el servidor esté listo (mismo patrón de reintento que Celery/RabbitMQ
    en el resto del proyecto).
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


def poblar_gestion_roles():
    """Inserta al analista fijo y a los clientes finales, manteniendo un
    customer_id de víctima reproducible y un esquema compatible con
    ms-identidad/logica/modelos.py:Usuario.
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
                usuarios.append(
                    (
                        customer_id,
                        fake.name(),
                        "cliente_final",
                        fake.country_code(representation="alpha-2"),
                        f"device-{customer_id.lower()}",
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
    """Genera perfiles dummy compatibles con ms-riesgo/logica/modelos.py.
    Mantiene un cliente víctima reproducible y el mismo identificador del
    flujo de seguridad para que el experimento sea consistente.
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
                score = random.randint(20, 95)
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
    print(f"seed: {len(_cliente_ids())} clientes y 1 analista sincronizados")
