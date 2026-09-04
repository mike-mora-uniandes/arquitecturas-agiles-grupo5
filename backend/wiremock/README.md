# wiremock

Simula Open Data / Open Finance para los escenarios de fallo del experimento.
El escenario **se elige por `customer_id`** (no por header); el mapeo es fijo.

`docker-compose.yml` monta `mappings/` y arranca con
`--global-response-templating` (para el `customer_id` dinámico del mapping por
defecto).

| `customer_id` | Escenario | Comportamiento |
|---|---|---|
| `C001` | ok | `200` con delay ~100 ms |
| `C002` | E1 timeout | 1º intento delay 1500 ms (timeout del cliente), luego se "recupera" (escenario stateful) → demuestra ASR3 |
| `C003`, `C004`, `C006` | E3 unavailable | `503` siempre |
| `C005` | E2 anomalous | `200` con payload que rompe el contrato (`data_risk` string / `financial_risk` ausente, `contract_version: "2.0"`) |
| otro | ok (por defecto) | `200` templado con el `customer_id` de la ruta |

Endpoints: `GET /open-data/customers/{id}` y `GET /open-finance/customers/{id}`.

## Pendiente

- Afinar payloads y añadir escenarios de fallo parcial (una fuente OK, otra caída).
- Si se necesita config propia, pasar el servicio a `build: ./wiremock`.
