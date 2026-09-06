# Wiremock

Simula las fuentes externas **Open Data** y **Open Finance** que consulta
`ms-perfil-riesgo`. Cada `customer_id` fija un escenario distinto; así una sola
corrida de carga ejercita línea base, timeout, reintento, enmascaramiento por
caché y payload anómalo sin tocar la configuración.

## Cómo se despliega

`docker-compose.yml` usa la imagen oficial `wiremock/wiremock:3.9.2`, monta
`./wiremock/mappings` en `/home/wiremock/mappings` (solo lectura) y arranca con:

```
--global-response-templating --disable-banner
```

`--global-response-templating` habilita `{{request.pathSegments.[2]}}` en el
mapping por defecto (devuelve el `customer_id` que venga en la ruta).

## Endpoints

| Método | Ruta | Devuelve |
|---|---|---|
| `GET` | `/open-data/customers/{customer_id}` | `customer_id`, `data_risk` (0–100), `negative_reports`, `history_length_months`, `generated_at`, `contract_version` |
| `GET` | `/open-finance/customers/{customer_id}` | `customer_id`, `financial_risk` (0–100), `monthly_income`, `debt_ratio`, `delinquencies_12m`, `generated_at`, `contract_version` |

`ms-perfil-riesgo` solo usa `data_risk` / `financial_risk` para el cálculo; el
resto de campos es relleno realista. La validación de esquema (ASR1 «anomalous»)
exige: `200` + JSON objeto + `customer_id` coincide + campo de riesgo presente,
numérico y en `0..100`.

## Matriz de escenarios (mapeo fijo por `customer_id`)

Las dos fuentes (`open-data.json` y `open-finance.json`) definen el **mismo**
escenario para cada cliente.

| `customer_id` | Escenario | Open Data | Open Finance | Efecto en el flujo |
|---|---|---|---|---|
| `C001` | OK (línea base) | `200`, `fixedDelay 100 ms` | `200`, `fixedDelay 100 ms` | cálculo en vivo → `OK` / `LIVE` |
| `C002` | Latencia aleatoria | `200`, `delayDistribution` lognormal `median 300 ms`, `sigma 0.6` | igual | la cola de la distribución supera a veces `DETECTION_TIMEOUT_MS` (700 ms) → timeout de cliente → **ASR1** + **ASR3**; si un reintento entra dentro del presupuesto → `OK` / `RETRY`, si no → `DEGRADED` / `CACHE` |
| `C003` | No disponible | `503` siempre | `503` siempre | fallo reintentable persistente → ASR1 + ASR3 agota → **ASR2** → `DEGRADED` / `CACHE` |
| `C004` | No disponible | `503` siempre | `503` siempre | igual que `C003`; el respaldo en Redis es más viejo (~20 h) pero válido |
| `C005` | Payload anómalo | `200`, `fixedDelay 90 ms`, `data_risk: "N/A"` (string), `contract_version "2.0"` | `200`, `fixedDelay 90 ms`, **sin** `financial_risk`, `contract_version "2.0"` | la validación de esquema falla en ambas → **no reintentable** → **ASR2** → `DEGRADED` / `CACHE` (span con `stale_version=true`, el respaldo de `C005` es `model_version v0`) |
| `C006` | No disponible | `503` siempre | `503` siempre | como `C003` pero **sin** clave `profile:C006` en Redis → `DEGRADED_NO_FALLBACK` / `CACHE` |
| cualquier otro | OK (por defecto) | `200`, `fixedDelay 100 ms`, `data_risk 25`, plantilla con el `customer_id` de la ruta | `200`, `fixedDelay 100 ms`, `financial_risk 30`, plantilla | cálculo en vivo → `OK` / `LIVE` |

Prioridades: los mappings específicos usan `priority 1`; la plantilla por defecto
`priority 10` (se aplica solo si ningún específico coincide).

## Comprobar a mano

```sh
curl -s http://localhost:8080/open-data/customers/C001    | jq
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/open-finance/customers/C003   # 503
```

## Pendiente

- Escenarios de **fallo parcial** (una fuente OK, la otra caída) con
  `customer_id` dedicados.
- Si hiciera falta configuración propia (extensiones, ficheros extra), pasar el
  servicio de `image:` a `build: ./wiremock` en `docker-compose.yml`.
