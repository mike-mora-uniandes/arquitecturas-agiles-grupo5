"""Puebla con datos dummy (Faker) las bases PostgreSQL del experimento:
GestiónRoles (ms-identidad) y PerfilRiesgo (ms-riesgo).

Idempotente: pensado para correr cada vez que se levanta el experimento
desde cero (`docker compose up`), igual espíritu que backend/redis/seed en
el experimento 1. Crea sus propias tablas (`CREATE TABLE IF NOT EXISTS`) en
vez de depender del orden de arranque de los microservicios.
"""
import os
import time

import psycopg2
from faker import Faker

fake = Faker("es_CO")

IDENTIDAD_DB_URL = os.environ["IDENTIDAD_DATABASE_URL"]
RIESGO_DB_URL = os.environ["RIESGO_DATABASE_URL"]

N_CLIENTES = int(os.getenv("SEED_N_CLIENTES", "10"))

ROLES = ["cliente_final", "cliente_final", "cliente_final", "analista_riesgo"]


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


def poblar_gestion_roles():
    """usuarios(customer_id, nombre, rol) — mismo esquema que
    ms-identidad/logica/modelos.py:Usuario.
    """
    conn = _conectar(IDENTIDAD_DB_URL)
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS usuarios (
                    customer_id VARCHAR PRIMARY KEY,
                    nombre VARCHAR NOT NULL,
                    rol VARCHAR NOT NULL
                )
                """
            )
            for i in range(1, N_CLIENTES + 1):
                customer_id = f"CLI-{i:04d}"
                cur.execute(
                    """
                    INSERT INTO usuarios (customer_id, nombre, rol)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (customer_id) DO NOTHING
                    """,
                    (customer_id, fake.name(), fake.random_element(ROLES)),
                )
    finally:
        conn.close()


def poblar_perfil_riesgo():
    # TODO: pendiente de que ms-riesgo defina su esquema de PerfilRiesgo
    # (score, categoría, datos personales, etc.) — coordinarlo con Jeffrey.
    pass


if __name__ == "__main__":
    poblar_gestion_roles()
    poblar_perfil_riesgo()
    print(f"seed: {N_CLIENTES} usuarios dummy generados en GestiónRoles")
