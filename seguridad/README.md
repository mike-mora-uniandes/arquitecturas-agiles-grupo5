# Backend Solventa — Experimento de seguridad

Experimento 2 del proyecto (el 1, de disponibilidad, vive en `../backend/` y
no se toca desde aquí). Evalúa la **confidencialidad** e **integridad** del
perfil de riesgo durante el flujo de consulta, materializando dos ataques
reales contra un stack en ejecución — mismo espíritu que el experimento de
disponibilidad: no se valida solo en papel.

| ASR | Atributo | Umbral |
|---|---|---|
| **ASR1** — detección | Confidencialidad | detectar la extracción no autorizada en `< 200 ms` |
| **ASR2** — detección | Integridad | detectar la alteración no autorizada en `< 500 ms` |
| **ASR3** — reacción | Confidencialidad | notificar al analista de riesgo en `< 5 s` desde la detección |
| **ASR4** — reacción | Integridad | notificar al analista de riesgo en `< 5 s` desde la detección |

## Arquitectura

```
analista ─POST /perfil-riesgo─▶ ms-cliente ─validar-usuario─▶ ms-identidad
                                     │  (BOLA deliberado: no compara
                                     │   customer_id_token vs. solicitado)
                                     ▼
                                mitmproxy ──▶ ms-riesgo   (altera una fracción
                                (siempre en          del perfil en tránsito,
                                 el camino)           MITM_ATTACK_RATIO)
                                     │
                        ValidadorIntegridad (hash HMAC)
                                     │
                ┌────────────────────┼────────────────────┐
                ▼                    ▼                     ▼
     ReporteSesionAccion   ReporteExtraccionPerfil   IntegridadFallida
     (ms-identidad)        (ms-riesgo)               (ms-cliente, si el
                │                    │                 hash no coincide)
                └────────────────────┴──────────┬──────────┘
                                                 ▼
                                             ms-audit
                              (empareja por request_id, detector
                               heurístico BOLA + comportamiento)
                                                 │
                                     incidente_seguridad
                                                 ▼
                                       ms-notificaciones
                                (notifica al analista, mide reacción)
```

- **`ms-identidad`** — autentica/autoriza; contiene la vulnerabilidad
  deliberada (BOLA) que el experimento explota.
- **`ms-cliente`** — punto de entrada síncrono; orquesta identidad + riesgo y
  verifica la integridad del perfil recibido.
- **`mitmproxy`** — simula el segmento de red comprometido entre `ms-cliente`
  y `ms-riesgo`; altera una fracción configurable de las respuestas.
- **`ms-riesgo`** — custodia el perfil de riesgo (dato sensible) y lo firma
  con un hash de integridad.
- **`ms-audit`** — único servicio que emite incidentes de seguridad; clasifica
  intrusiones y mide ASR1/ASR2.
- **`ms-notificaciones`** — entrega el incidente al analista y mide ASR3/ASR4.
- **Infra**: RabbitMQ (broker), 3 Postgres (uno por servicio con estado), y —
  en el perfil `experimento` — OTel Collector + Prometheus + Grafana, con
  Locust como generador de tráfico de ataque.

## Estado

Los 4 ASR están implementados y verificables end-to-end contra el stack
levantado (ver «Ejecutar el experimento con métricas» más abajo).

| Componente | Estado |
|---|---|
| Estructura + `docker-compose` + imagen base | ✅ |
| `ms-identidad` (`ValidarUsuario` + BOLA deliberado) | ✅ |
| `ms-cliente` (orquestación + `ValidadorIntegridad` + productor `IntegridadFallida`) | ✅ |
| `ms-riesgo` (`SolicitarPerfil` + `GeneradorIntegridad`) | ✅ |
| `mitmproxy` (altera perfiles en tránsito, `MITM_ATTACK_RATIO`) | ✅ |
| **`ms-audit`** (detector heurístico BOLA + comportamiento, clasifica y publica el incidente) | ✅ consumidores + PostgreSQL + clasificador + métricas |
| **`ms-notificaciones`** (notifica al analista) | ✅ consume incidente + métrica de reacción |
| **Observabilidad** (OTel + Prometheus + Grafana) | ✅ pipeline + dashboard por ASR (perfil `experimento`) |
| `seed/` (datos dummy con Faker, 3 bases) | ✅ ver [`seed/README.md`](seed/README.md) |
| `experimento/` (`forjar_token.py`, `mitm_alterar_perfil.py`, `locustfile.py`) | ✅ ver [`experimento/README.md`](experimento/README.md) |

Contrato del evento `IntegridadFallida` (`ms-cliente` → `ms-audit`):
[`ms-audit/README.md`](ms-audit/README.md#contrato-del-evento-integridadfallida).

## Decisiones de alcance pendientes de confirmar con el equipo

Quedaron abiertas en la revisión del diseño, antes de construir a fondo:

1. **Bloqueo del atacante en `ms-identidad`** (Revoke Access) — la narrativa
   original lo mencionaba, pero hoy ni los 4 ASR ni la arquitectura lo cubren.
   ¿Se agrega un ASR5, o se deja fuera de alcance a propósito?
2. **Firma de los mensajes del broker de auditoría/notificación** — solo el
   perfil de riesgo va firmado (hash); los reportes hacia `ms-audit` y la
   notificación hacia `ms-notificaciones` viajan sin firmar. ¿Queda como
   limitación documentada, o se firma también ese canal?
3. **Riesgo de latencia**: ASR1 (200 ms) se detecta por el camino
   **asíncrono** (`ms-riesgo`/`ms-identidad` → broker → `ms-audit` clasifica);
   ASR2 (500 ms) se detecta **síncrono e inline** en `ms-cliente`. El camino
   async tiene más saltos y un umbral más estricto — medir esto temprano
   (spike, ya asignado en el reparto de tareas) antes de dar los números por
   buenos.

## Estructura

```
seguridad/
├── README.md
├── docker-compose.yml
├── build-base.sh
├── .env.example
│
├── base-image/          # solventa/security-flask-base (propia de este experimento)
├── seed/                 # Faker — puebla ms-identidad-db, ms-riesgo-db y ms-audit-db
├── experimento/          # forjar_token.py (PyJWT) + mitm_alterar_perfil.py (mitmproxy)
│
├── ms-identidad/          # GestiónRoles + Autenticación/Autorización + GestionUsuarios
├── ms-cliente/            # GestionClientes + ValidadorIntegridad — punto de entrada
├── ms-riesgo/             # PerfilRiesgo + GeneradorIntegridad
├── ms-audit/              # HistorialRegistrosUsuario + HistorialConexion
└── ms-notificaciones/     # entrega el incidente al analista de riesgo
```

Cada `ms-*/` sigue el mismo layout plano que `../backend/`: `app.py`,
`config.py`, `extensiones.py`, `run.sh`, `Dockerfile`, `vistas/ logica/
tareas/ tests/`. Solo `ms-audit` y `ms-notificaciones` corren worker de
Celery (consumen del broker) — `ms-identidad` y `ms-riesgo` son productores
puros (publican con `send_task`, sin worker), y `ms-cliente` no toca el
broker en absoluto (todo su tráfico es HTTP síncrono).

## Servicios y puertos

Puertos de host distintos a `../backend/` a propósito, para poder levantar
ambos experimentos al mismo tiempo.

| Servicio | Host:contenedor | Descripción |
|---|---|---|
| `ms-identidad` | `6001:5000` | identifica, autentica y autoriza |
| `ms-cliente` | `6002:5000` | punto de entrada del flujo |
| `ms-riesgo` | `6003:5000` | perfil de riesgo + firma de integridad |
| `ms-audit` | `6004:5000` | clasifica intrusiones, publica el incidente |
| `ms-notificaciones` | `6005:5000` | notifica al analista de riesgo |
| `rabbitmq` | `5673`, `15673` | broker AMQP (consola `guest`/`guest`) |
| `ms-identidad-db` / `ms-riesgo-db` / `ms-audit-db` | `5433` / `5434` / `5435` | PostgreSQL, uno por servicio |
| `grafana` / `prometheus` | `3001` / `9091` | solo con `--profile experimento` |
| `otel-collector` | `4319`, `9465` | OTLP http + `/metrics` (perfil `experimento`) |

## Puesta en marcha

```sh
cd seguridad
sh build-base.sh
```

El script crea `.env` desde `.env.example`, construye
`solventa/security-flask-base` y levanta el stack (incluye el `seed` con
Faker, que corre una vez y termina).

Detener: `docker compose down` (o `docker compose down -v` para también
borrar los datos de las 3 bases).

## Ejecutar el experimento con métricas (observabilidad)

Para medir los ASR en Grafana en vivo:

1. Activar la telemetría en `.env`:

   ```
   OTEL_SDK_DISABLED=false
   OTEL_TRACES_EXPORTER=otlp
   OTEL_METRICS_EXPORTER=otlp
   ```

2. Levantar el stack completo (añade `otel-collector`, `prometheus`, `grafana`):

   ```sh
   docker compose --profile experimento up -d --build
   ```

3. Ejecutar los ataques (ver [`experimento/`](experimento/README.md)) y abrir
   el dashboard **Solventa · Experimento de seguridad** en
   http://localhost:3001 → detección (ASR1/ASR2) vs. su umbral y notificación
   (ASR3/ASR4) vs. 5 s, con el `% que cumple` de cada uno.

Evidencia sin Grafana: `docker compose logs -f ms-audit ms-notificaciones`
muestra las líneas `INTRUSION ...` y `NOTIFICAR ANALISTA ...`, y
`GET http://localhost:6004/incidentes` lista los incidentes clasificados.
