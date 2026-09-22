# ms-riesgo

Andamiaje: el servicio construye y arranca, sin endpoints ni lógica de
negocio todavía.

**Propósito final:** custodiar y entregar el perfil de riesgo del cliente
(datos sensibles, PII) junto con evidencia verificable de su integridad, y
dejar registro de cada extracción atendida. Solo accesible por `ms-cliente`,
nunca directamente desde fuera — es el objetivo del ataque de
confidencialidad (ASR1) del experimento.

**Comportamiento esperado:** recibe de `ms-cliente` la "solicitud de perfil",
consulta la base de datos `PerfilRiesgo` (PostgreSQL) y responde el perfil de
riesgo junto con su hash de integridad (`logica/generador_integridad.py`). De
forma asíncrona publica `ReporteExtraccionPerfilRiesgoCliente` en el Event Bus
(lo consume `ms-audit`).

Pendiente:
- Modelo de datos `PerfilRiesgo` en PostgreSQL + seed (ver `../seed/`).
- Endpoint `SolicitarPerfil`.
- `GeneradorIntegridad`: firma del payload (hashlib/hmac).
- Publicación de `ReporteExtraccionPerfilRiesgoCliente` al Event Bus.
