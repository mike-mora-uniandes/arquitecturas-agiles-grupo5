# seed

Servicio one-shot (`docker compose up` lo corre y termina, `depends_on:
service_completed_successfully` bloquea a `ms-identidad`, `ms-riesgo` y
`ms-audit` hasta que termina) que puebla con datos dummy generados con
**Faker** las tres bases PostgreSQL del experimento: `ms-identidad-db`
(`usuarios`/`roles`), `ms-riesgo-db` (`perfiles_riesgo`) y `ms-audit-db`
(`historial_conexion`, la línea base de comportamiento «normal» que usa el
detector heurístico de `ms-audit`).

## `generar_seed.py`

Reproducible vía `SEED_SEED` (semilla de `random`/`Faker`). Dos escenarios
(`SEED_SCENARIO`, ver `../.env.example`):

| Escenario | `attack_ratio` | Efecto |
|---|---|---|
| `baseline` | `0.05` | casi todo el tráfico/perfiles son legítimos |
| `attack` (default) | `SEED_ATTACK_RATIO` (`0.20`) | marca `CLI-0002`–`CLI-0004` como sospechosos (puntaje 70–95) para ejercitar la detección |

Tres pasos, cada uno idempotente (`ON CONFLICT DO NOTHING` / guard por
conteo) y con DDL defensiva (`CREATE TABLE IF NOT EXISTS` +
`ALTER ... ADD COLUMN IF NOT EXISTS`) porque compite en el arranque con el
`create_all` de cada microservicio:

1. **`poblar_gestion_roles()`** — roles + `SEED_N_CLIENTES` clientes
   (`CLI-0001`…) más un analista fijo (`ANL-0001`) en `ms-identidad-db`, cada
   uno con su `pais_habitual`/`device_habitual` (`CO` / `desktop-linux`,
   igual que el tráfico legítimo de `locustfile.py`, para que la detección
   por comportamiento no marque como anómalo el tráfico normal).
2. **`poblar_perfil_riesgo()`** — un perfil de riesgo por cliente en
   `ms-riesgo-db`, con `puntaje`/`categoria` según si el escenario lo marca
   sospechoso.
3. **`poblar_historial_audit()`** — `SEED_HISTORIAL_NORMALES` conexiones
   "normales" por cliente en `ms-audit-db.historial_conexion`, para que el
   detector de comportamiento de `ms-audit` tenga línea base desde la
   primera request (arranque en frío). Si la tabla ya tiene filas, no
   duplica — `ms-audit` también auto-siembra como respaldo
   (`AUTOSEED_*`), este guard evita que ambos se pisen.

## Variables de entorno (ver `../.env.example`)

`IDENTIDAD_DATABASE_URL`, `RIESGO_DATABASE_URL`, `AUDIT_DATABASE_URL`,
`SEED_N_CLIENTES`, `SEED_SCENARIO`, `SEED_SEED`, `SEED_ATTACK_RATIO`,
`SEED_HISTORIAL_NORMALES`.

## Probar en vivo

```sh
docker compose logs seed
# seed: escenario=attack ratio_ataques=0.2 clientes=10 (identidad + riesgo + historial audit)
```

Para repoblar desde cero (p. ej. tras cambiar `SEED_SCENARIO`), reiniciar los
volúmenes de datos: `docker compose down -v && sh build-base.sh`.
