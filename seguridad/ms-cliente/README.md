# ms-cliente

Andamiaje: el servicio construye y arranca, sin endpoints ni lógica de
negocio todavía.

**Propósito final:** ser el punto de entrada del flujo. Ninguna solicitud
avanza ni retorna datos hasta que el actor sea identificado y validado por
`ms-identidad`; una vez validado, solicita el perfil a `ms-riesgo` y verifica
su hash de integridad antes de responder.

**Comportamiento esperado:** recibe la solicitud (`IConsultarPerfilRiesgoService`)
y pide la validación a `ms-identidad`. Si el usuario es rechazado, responde el
rechazo sin solicitar el perfil. Si es validado, solicita el perfil a
`ms-riesgo`; `ValidadorIntegridad` (`logica/validador_integridad.py`)
recalcula el hash recibido y lo compara. Si no coincide, detecta una
manipulación no autorizada del perfil (ASR2).

Sin broker: es el único componente del experimento que no publica ni consume
eventos — toda su comunicación es HTTP síncrona.

Pendiente:
- Orquestación completa del flujo (llamar a `ms-identidad`, luego a `ms-riesgo`).
- `ValidadorIntegridad`: comparación de hash (hashlib/hmac).
- Manejo del caso de rechazo por identidad y del caso de integridad fallida.
