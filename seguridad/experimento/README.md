# experimento

Scripts que materializan los dos ataques del experimento — **no son
servicios de `docker-compose`**, se ejecutan manualmente contra el stack ya
levantado, igual que se hizo con las pruebas manuales del experimento 1.

| Script | Escenario | ASR |
|---|---|---|
| `locustfile.py` | Confidencialidad — carga con mezcla legít/BOLA/anomalía (servicio `locust`) | ASR1 / ASR3 |
| `forjar_token.py` | Confidencialidad — token forjado (PyJWT), extracción no autorizada puntual | ASR1 / ASR3 |
| `mitm_alterar_perfil.py` | Integridad — addon de mitmproxy que altera el `puntaje` del perfil en tránsito | ASR2 / ASR4 |

> **`forjar_token.py` está desactualizado**: quedó escrito antes de que
> `ms-cliente` existiera y todavía apunta a `http://localhost:5000` +
> `GET /perfiles/{customer_id}` con el token en un header `Authorization`.
> El contrato real es `POST http://localhost:6002/perfil-riesgo` con
> `token`/`customer_id`/`ip`/`device`/`pais` en el body JSON (el mismo que
> usa `locustfile.py`, caso `unauthorized`) — el script necesita ese ajuste
> antes de poder usarse tal cual.

## Confidencialidad (ASR1/ASR3)

Con el stack arriba (`docker compose --profile experimento up -d`), abrir
Locust en http://localhost:8089 (escenario `attack` por defecto, incluye el
caso `unauthorized` — token válido de un cliente pidiendo el perfil de otro)
es hoy la forma confiable de ejercitar el ASR1/ASR3. Para un disparo puntual
manual con el mismo contrato, mientras `forjar_token.py` no se actualice:

```sh
python3 -c "import jwt; print(jwt.encode({'customer_id': 'CLI-0002'}, 'change-me', algorithm='HS256'))"
curl -s -XPOST http://localhost:6002/perfil-riesgo \
  -H 'Content-Type: application/json' \
  -d '{"token":"<token de CLI-0002>","customer_id":"CLI-0001","ip":"1.2.3.4","device":"unknown-device","pais":"IR"}'
```

`ms-audit` clasifica la intrusión (BOLA o comportamiento anómalo vs.
habitual) y `ms-notificaciones` notifica; evidencia en
`GET http://localhost:6004/incidentes` o
`docker compose logs -f ms-audit ms-notificaciones`.

## Integridad (ASR2/ASR4) — mitmproxy siempre en el camino

`mitmproxy` está **siempre** desplegado entre `ms-cliente` y `ms-riesgo`
(simula el segmento de red comprometido); `ms-cliente` apunta a él por defecto.
Altera solo una **fracción** de los perfiles en tránsito, controlada por
`MITM_ATTACK_RATIO` en `.env`:

| `MITM_ATTACK_RATIO` | Efecto |
|---|---|
| `0` | passthrough — flujo funcional puro, sin integridad |
| `0.2` (default) | ~20% de las respuestas se alteran → integridad se ejercita **junto** a confidencialidad en la misma corrida de Locust |
| `1.0` | todo se altera → corrida dedicada de integridad |

Así, **una sola corrida de Locust** ejercita los 4 ASR: la mayoría del tráfico
pasa intacto (confidencialidad: BOLA / comportamiento) y la fracción alterada
falla el hash → `ms-cliente` publica `IntegridadFallida` → `ms-audit` mide
(ASR2) → `ms-notificaciones` notifica (ASR4).

Evidencia: `docker compose logs ms-audit ms-notificaciones` (líneas
`INTRUSION integridad` / `ASR4`) y `GET http://localhost:6004/incidentes`.
