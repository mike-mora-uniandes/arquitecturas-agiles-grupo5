# ms-identidad

Andamiaje: el servicio construye y arranca, sin endpoints ni lógica de
negocio todavía.

**Propósito final:** identificar, autenticar y autorizar a los actores que
solicitan un perfil de riesgo, rechazando a quienes no tengan acceso, y dejar
trazabilidad de cada sesión y acción.

**Comportamiento esperado:** recibe de `ms-cliente` la solicitud de
"Autenticación y validación de usuario" (`ValidaIdentidad`), verifica la
identidad y los permisos sobre el perfil consultado, y responde "usuario
validado" o rechazo. De forma asíncrona publica `ReporteSesionAccion` en el
Event Bus (lo consume `ms-audit`).

Pendiente:
- Endpoint `ValidarUsuario` (síncrono, llamado por `ms-cliente`).
- Modelo de datos de `GestiónRoles` (roles y permisos) en PostgreSQL.
- Emisión y validación de tokens de sesión (PyJWT) — el escenario de
  confidencialidad del experimento depende de que este token sea forjable
  de forma controlada para simular el bypass.
- Publicación de `ReporteSesionAccion` al Event Bus.
