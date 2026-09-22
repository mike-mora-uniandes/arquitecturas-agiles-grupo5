"""Puebla con datos dummy (Faker) las 3 bases PostgreSQL del experimento:
GestiónRoles (ms-identidad), PerfilRiesgo (ms-riesgo) y Audit (ms-audit).

Idempotente: pensado para correr cada vez que se levanta el experimento
desde cero (`docker compose up`), igual espíritu que backend/redis/seed en
el experimento 1.
"""
import os

from faker import Faker

fake = Faker("es_CO")

IDENTIDAD_DB_URL = os.environ["IDENTIDAD_DATABASE_URL"]
RIESGO_DB_URL = os.environ["RIESGO_DATABASE_URL"]
AUDIT_DB_URL = os.environ["AUDIT_DATABASE_URL"]

N_CLIENTES = int(os.getenv("SEED_N_CLIENTES", "10"))


def poblar_gestion_roles():
    # TODO: insertar N_CLIENTES usuarios + un rol "cliente_final" y uno
    # "analista_riesgo" en GestiónRoles (ms-identidad).
    pass


def poblar_perfil_riesgo():
    # TODO: insertar N_CLIENTES perfiles de riesgo (customer_id, score,
    # categoría, datos personales) en PerfilRiesgo (ms-riesgo) — este es el
    # dato sensible que protege el experimento de confidencialidad.
    pass


if __name__ == "__main__":
    poblar_gestion_roles()
    poblar_perfil_riesgo()
    print(f"seed: {N_CLIENTES} clientes dummy generados con Faker")
