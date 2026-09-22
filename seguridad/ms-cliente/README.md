# ms-cliente

Implementado: orquestación `IConsultarPerfilRiesgoService` (MS Identidad ->
MS Riesgo) + `ValidadorIntegridad`. Sin broker: es el único componente del
experimento que no publica ni consume eventos — toda su comunicación es
HTTP síncrona. Instrumentado con OpenTelemetry (`run.sh`).

**Propósito:** ser el punto de entrada del flujo. Ninguna solicitud avanza
ni retorna datos hasta que el actor sea identificado y validado por
`ms-identidad`; una vez validado, solicita el perfil a `ms-riesgo` y
verifica su hash de integridad antes de responder.

## `POST /perfil-riesgo`

```json
// Request
{ "token": "<JWT>", "customer_id": "CLI-0007",
  "ip": "1.2.3.4", "device": "iPhone", "pais": "CO" }   // ip/device/pais opcionales

// Response 200 — perfil de ms-riesgo, ya verificado
{ "customer_id": "CLI-0007", "nombre_completo": "...", "documento_identidad": "...",
  "puntaje": 80, "categoria": "ALTO", "actualizado_en": "...", "hash_integridad": "..." }

// Response 401 — rechazado por ms-identidad
{ "error": "..." }
// Response 404 — customer_id sin perfil en ms-riesgo
{ "error": "perfil 'CLI-0007' no encontrado" }
// Response 502 — hash de integridad no coincide (perfil alterado en tránsito, ASR2)
{ "error": "el perfil recibido no superó la verificación de integridad" }
```

Ruta propuesta por este servicio (no viene de ningún diagrama previo) — el
API Gateway del diseño aún no existe, así que puede renombrarse sin costo
cuando se implemente.

## Comportamiento esperado (`logica/orquestador.py`)

1. Llama a `POST {MS_IDENTIDAD_URL}/validar-usuario` (contrato real de
   `ms-identidad`, ver su README). Si `validado` es `false`, rechaza sin
   llamar a `ms-riesgo`.
2. Si es `true`, pide el perfil a `GET {MS_RIESGO_URL}/perfiles/<customer_id>`.
3. `ValidadorIntegridad` (`logica/validador_integridad.py`) recalcula el
   hash del perfil recibido y lo compara contra `hash_integridad`. Si no
   coincide, detecta una manipulación no autorizada del perfil (ASR2).

**No verifica** que `customer_id_token` (dueño real del token) coincida con
`customer_id` (perfil solicitado) — esa comprobación se omite a propósito en
`ms-identidad` (BOLA deliberado, ver su README) y su detección es
responsabilidad de `ms-audit`, no de este servicio.

## Variables de entorno (ver `../.env.example`)

`MS_IDENTIDAD_URL`, `MS_RIESGO_URL`, `INTEGRITY_SECRET` (mismo secreto que
`ms-riesgo`), `LOG_LEVEL`.

## Pruebas

```sh
cd ms-cliente
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest tests
```

`requests` mockeado (`test_orquestador.py`: rechazo de identidad, éxito,
perfil no encontrado, hash alterado) — no necesitan `ms-identidad` ni
`ms-riesgo` corriendo.

Pendiente:
- Corrida end-to-end en `docker compose` contra `ms-identidad` real (PR #41
  de Michael, aún no mergeado a `develop`) y datos de `../seed/` (a cargo de
  Lorena).
