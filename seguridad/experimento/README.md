# experimento

Scripts que materializan los dos ataques del experimento — **no son
servicios de `docker-compose`**, se ejecutan manualmente contra el stack ya
levantado, igual que se hizo con las pruebas manuales del experimento 1.

| Script | Escenario | ASR |
|---|---|---|
| `locustfile.py` | Confidencialidad — carga con mezcla legít/BOLA/anomalía (servicio `locust`) | ASR1 / ASR3 |
| `forjar_token.py` | Confidencialidad — token forjado (PyJWT), extracción no autorizada puntual | ASR1 / ASR3 |
| `mitm_alterar_perfil.py` | Integridad — addon de mitmproxy que altera el `puntaje` del perfil en tránsito | ASR2 / ASR4 |

## Confidencialidad (ASR1/ASR3)

Con el stack arriba (`docker compose --profile experimento up -d`), abrir
Locust en http://localhost:8089 (escenario `attack` por defecto) o correr
`forjar_token.py` para un disparo puntual. `ms-audit` clasifica la intrusión
(BOLA o comportamiento anómalo vs. habitual) y `ms-notificaciones` notifica.

## Integridad (ASR2/ASR4) — con mitmproxy

El ataque altera el perfil en tránsito entre `ms-cliente` y `ms-riesgo`. Se
levanta `mitmproxy` como reverse-proxy y se repunta `ms-cliente` a través de
él con el override `../docker-compose.integridad.yml` (solo durante esta
corrida, para no ensuciar el flujo normal):

```sh
# activar el ataque de integridad
docker compose -f docker-compose.yml -f docker-compose.integridad.yml \
    up -d --force-recreate ms-cliente mitmproxy

# cualquier petición a ms-cliente devuelve el perfil manipulado ->
# el hash no coincide -> ms-cliente publica IntegridadFallida ->
# ms-audit mide (ASR2) y ms-notificaciones notifica (ASR4)
curl -s -XPOST http://localhost:6002/perfil-riesgo -H 'Content-Type: application/json' \
  -d '{"token":"<jwt>","customer_id":"CLI-0005","ip":"10.0.0.5","device":"desktop-linux","pais":"CO"}'

# volver al flujo normal (sin mitm)
docker compose up -d --force-recreate ms-cliente
docker compose stop mitmproxy
```

Evidencia: `docker compose logs ms-audit ms-notificaciones` (líneas
`INTRUSION integridad` / `ASR4`) y `GET http://localhost:6004/incidentes`.
