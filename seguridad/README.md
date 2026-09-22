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

## Estado

Puro andamiaje — ningún servicio tiene lógica de negocio todavía. Ver el
reparto de tareas del equipo (Michael/Jeffrey/Daniel/Lorena) para el orden
de construcción.

| Componente | Estado |
|---|---|
| Estructura + `docker-compose` + imagen base | ✅ |
| `ms-identidad` / `ms-cliente` / `ms-riesgo` / `ms-audit` / `ms-notificaciones` | ⏳ andamiaje |
| `seed/` (datos dummy con Faker) | ⏳ andamiaje |
| `experimento/` (forjar token, mitmproxy) | ⏳ plantillas sin implementar |
| Observabilidad (OTel + Prometheus + Grafana) | ⏳ no scaffoldeado — reutilizar el patrón de `../backend/observabilidad/` cuando se llegue a esa tarea |

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
├── seed/                 # Faker — puebla ms-identidad-db y ms-riesgo-db
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
