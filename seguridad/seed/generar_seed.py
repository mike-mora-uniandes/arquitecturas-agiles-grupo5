"""Puebla con datos dummy (Faker) las 3 bases PostgreSQL del experimento:
GestiónRoles (ms-identidad), PerfilRiesgo (ms-riesgo) y Audit (ms-audit).

Idempotente: pensado para correr cada vez que se levanta el experimento
desde cero (`docker compose up`), igual espíritu que backend/redis/seed en
el experimento 1.
"""
import os
import random

from faker import Faker
import psycopg2

fake = Faker("es_CO")

IDENTIDAD_DB_URL = os.environ["IDENTIDAD_DATABASE_URL"]
RIESGO_DB_URL = os.environ["RIESGO_DATABASE_URL"]
AUDIT_DB_URL = os.environ["AUDIT_DATABASE_URL"]

N_CLIENTES = int(os.getenv("SEED_N_CLIENTES", "10"))

VICTIMA_CUSTOMER_ID = "CLI-0001"
ANALISTA_CUSTOMER_ID = "ANL-0001"


def _cliente_ids():
    return [f"CLI-{indice:04d}" for indice in range(1, N_CLIENTES)]


def _categoria_para_score(score: int) -> str:
    if score >= 80:
        return "alto"
    if score >= 50:
        return "medio"
    return "bajo"


def poblar_gestion_roles():
    # Inserta N_CLIENTES usuarios con un analista fijo y el resto clientes
    # finales, para dejar un customer_id de víctima reproducible.
    with psycopg2.connect(IDENTIDAD_DB_URL) as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS roles (
                    nombre TEXT PRIMARY KEY
                )
                """
            )
            cursor.execute(
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
            cursor.executemany(
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

            cursor.executemany(
                """
                INSERT INTO usuarios (
                    customer_id, nombre, rol, pais_habitual, device_habitual
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (customer_id) DO NOTHING
                """,
                usuarios,
            )


def poblar_perfil_riesgo():
    # Inserta un perfil por cada cliente final, con el mismo customer_id que
    # se usa en GestiónRoles para mantener el flujo consistente.
    with psycopg2.connect(RIESGO_DB_URL) as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS perfiles_riesgo (
                    customer_id TEXT PRIMARY KEY,
                    score INTEGER NOT NULL,
                    categoria TEXT NOT NULL,
                    nombre TEXT NOT NULL,
                    email TEXT NOT NULL,
                    direccion TEXT NOT NULL
                )
                """
            )

            perfiles = []
            for customer_id in _cliente_ids():
                score = random.randint(20, 95)
                perfiles.append(
                    (
                        customer_id,
                        score,
                        _categoria_para_score(score),
                        fake.name(),
                        fake.email(),
                        fake.address().replace("\n", ", "),
                    )
                )

            cursor.executemany(
                """
                INSERT INTO perfiles_riesgo (
                    customer_id, score, categoria, nombre, email, direccion
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (customer_id) DO NOTHING
                """,
                perfiles,
            )


if __name__ == "__main__":
    poblar_gestion_roles()
    poblar_perfil_riesgo()
    print(f"seed: {N_CLIENTES} clientes dummy generados con Faker")
