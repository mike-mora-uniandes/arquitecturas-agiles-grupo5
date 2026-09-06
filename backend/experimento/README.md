# Experimento

Generación de carga para el experimento de disponibilidad. Un *virtual user* de
Locust imita al analista: hace `POST /evaluations` a `ms-riesgos` con un
`customer_id` de la matriz y **no** espera el resultado (el flujo es asíncrono;
la evidencia de los ASR sale de Grafana).

## Archivos

| Archivo | Rol |
|---|---|
| `locustfile.py` | `AnalystUser` (`wait_time` 1–3 s). Cada `task` elige un escenario según pesos y hace `POST /evaluations` con `name=/evaluations/<Ei>` para separarlo en las estadísticas. |
| `run_asr_tests.ps1` | Helper PowerShell: fija los `E*_WEIGHT` para enfatizar un ASR (`ASR1` / `ASR2` / `ASR3` / `BASE`) e imprime los ajustes sugeridos de Locust. **No arranca Locust.** |
| `test_locust_scenarios.py` | `pytest`: valida que la matriz `E0`–`E3` existe y que `pick_scenario()` devuelve un escenario válido. |

## Matriz de escenarios

Cada `Ei` mapea a un `customer_id`; ese id selecciona el escenario de Wiremock
(mismo comportamiento en Open Data y Open Finance).

| Peso | Escenario | `customer_id` | Wiremock | ASR ejercitadas | `status` / `source` esperado |
|---|---|---|---|---|---|
| `E0_WEIGHT` (40) | línea base | `C001` | `200`, ~100 ms | — | `OK` / `LIVE` |
| `E1_WEIGHT` (18) | latencia aleatoria | `C002` | lognormal `median 300 ms` `sigma 0.6` | ASR1 + ASR3 | `OK` / `RETRY` o `DEGRADED` / `CACHE` |
| `E2_WEIGHT` (15) | no disponible | `C003` | `503` | ASR1 + ASR3 → ASR2 | `DEGRADED` / `CACHE` |
| `E3_WEIGHT` (15) | no disponible | `C004` | `503` | ASR2 (respaldo viejo válido) | `DEGRADED` / `CACHE` |
| `E4_WEIGHT` (8) | payload anómalo | `C005` | `200` con contrato roto | ASR1 → ASR2 | `DEGRADED` / `CACHE` (`stale_version=true`) |
| `E5_WEIGHT` (4) | sin respaldo | `C006` | `503`, sin clave en Redis | ASR2 sin caché | `DEGRADED_NO_FALLBACK` / `CACHE` |

Los pesos entre paréntesis son los valores por defecto del `locustfile.py`.

## Cómo ejecutar

### Opción A — Locust dentro de compose (por defecto)

El servicio `locust` ya está en `docker-compose.yml` (perfil core y experimento),
apuntando a `http://ms-riesgos:5000`.

```sh
docker compose --profile experimento up -d
# abrir http://localhost:8089 y pulsar Start
```

Para cambiar los pesos hay que añadir un bloque `environment:` con los
`E*_WEIGHT` al servicio `locust` en `docker-compose.yml` y recrear el contenedor
(**`locust` no lee `.env`**).

### Opción B — Locust en local (permite `run_asr_tests.ps1`)

```powershell
pip install locust
.\experimento\run_asr_tests.ps1 ASR2         # fija los E*_WEIGHT en la sesión
locust -f .\experimento\locustfile.py --host http://localhost:5001
# abrir http://localhost:8089
```

## Formulario de Locust («Start new load test»)

En http://localhost:8089, la pantalla inicial pide:

| Campo | Significado | Ejemplo (prueba rápida) |
|---|---|---|
| **Number of users (peak concurrency)** | usuarios concurrentes máximos | `10` |
| **Ramp up (users started/second)** | usuarios nuevos por segundo hasta llegar al total | `5` |
| **Host** | destino; ya relleno con `http://ms-riesgos:5000` (en local: `http://localhost:5001`) | `http://ms-riesgos:5000` |
| **Advanced options → Run time** | duración de la corrida (`20s`, `2m`, `5m`, `1h20m`…); vacío = hasta *Stop* | `5m` |

Pulsar **START**. La cabecera muestra `STATUS` (`READY` → `RUNNING`), `RPS` y
`FAILURES`. `FAILURES` cuenta respuestas no-2xx de `ms-riesgos` y **debe quedar
en `0%`**: un resultado `DEGRADED` sigue siendo `202` para la API, la degradación
solo se ve en Grafana. Al acabar, *Download Data* (CSV) y *Report* (HTML) quedan
disponibles.

## Fases sugeridas (`../DESIGN.md` §2.5)

Una corrida por fila (rellenando el formulario de arriba):

| Fase | Number of users | Ramp up | Run time | Mezcla |
|---|---|---|---|---|
| Baseline | 5 | 1 | 2m | solo `C001` (resto de pesos a 0) |
| Carga con fallos | 20–30 | 2 | 5m–10m | matriz `E0`–`E5` por defecto |
| Pico (opcional) | 50 | 5 | 3m | misma mezcla |

Aceptación en Locust: p95 del `202` de `ms-riesgos` `< ~50 ms` (el trabajo pesado
ocurre en el worker, fuera del camino de la petición).

Entre corridas: `docker compose --profile experimento down -v` para repoblar
Redis y limpiar colas y métricas.

## Dónde se leen los resultados

Grafana → http://localhost:3000 → *«Solventa - Experimento de disponibilidad
(PerfilRiesgo)»*. Ver `../observabilidad/grafana/provisioning/dashboards/README.md`.
