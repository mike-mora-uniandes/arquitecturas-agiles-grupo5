# ms-identidad

Implementado: `ValidarUsuario` + publicación de `ReporteSesionAccion`.
Productor puro (usa Celery como cliente, no corre worker — ver `run.sh`).

**Propósito:** identificar, autenticar y autorizar a los actores que
solicitan un perfil de riesgo, y dejar trazabilidad de cada sesión y acción.

## `POST /validar-usuario`

```json
// Request
{
  "token": "<JWT firmado con JWT_SECRET>",
  "customer_id_solicitado": "CLI-0007",
  "ip": "1.2.3.4",       // opcional, dummy
  "device": "iPhone",     // opcional, dummy
  "pais": "CO"             // opcional, dummy
}

// Response 200
{ "validado": true, "customer_id_token": "CLI-0003" }

// Response 401 (firma inválida o customer_id_token no existe en GestiónRoles)
{ "validado": false, "error": "..." }
```

## La vulnerabilidad deliberada (ASR1/ASR3 — confidencialidad)

`ValidarUsuario` verifica que el JWT esté bien firmado y que el
`customer_id` del token exista en `GestiónRoles` — pero **a propósito no
compara** `customer_id_token` contra `customer_id_solicitado`. Un token
válido de cualquier cliente sirve para pedir el perfil de cualquier otro
(BOLA). Ver `logica/validar_usuario.py` para el detalle.

La detección **no** ocurre acá: `ReporteSesionAccion` se publica con
**ambos** customer_id en cada intento (exitoso o rechazado), y es
`ms-audit` quien correlaciona la anomalía (`customer_id_token !=
customer_id_solicitado`) aguas abajo.

## Qué publica (`tareas/publicacion.py`)

| | valor |
|---|---|
| tarea Celery consumida por | `audit.registrar_sesion_accion` (`Config.SESION_ACCION_TASK_NAME`) |
| cola | `audit.sesion_accion.q` (la declara este servicio y `ms-audit`, deben coincidir) |
| exchange / routing key | `solventa-seguridad` (topic) / `identidad.sesion_accion` |

## Modelo de datos (`logica/modelos.py`)

`usuarios(customer_id PK, nombre, rol)` — poblado por `../seed/`. Sin
login real (usuario/contraseña): el login/auth es dummy a propósito, para
poder simular la violación de accesos sin depender de una implementación
de autenticación completa.

## Variables de entorno (ver `../.env.example`)

`IDENTIDAD_DATABASE_URL`, `JWT_SECRET`, `RABBITMQ_URL`, `RABBITMQ_EXCHANGE`
(`solventa-seguridad`), `SESION_ACCION_QUEUE`, `SESION_ACCION_ROUTING_KEY`,
`SESION_ACCION_TASK_NAME`, `LOG_LEVEL`.

## Probar en vivo

```sh
# token legítimo de CLI-0001 pidiendo el perfil de CLI-0007 (otro cliente)
python3 -c "
import jwt
print(jwt.encode({'customer_id': 'CLI-0001'}, 'change-me', algorithm='HS256'))
"
curl -s -XPOST http://localhost:6001/validar-usuario \
  -H 'Content-Type: application/json' \
  -d '{"token": "<pegar el token>", "customer_id_solicitado": "CLI-0007"}'
```

Pendiente:
- Ninguno para este endpoint — falta que `ms-cliente` lo consuma en su
  orquestación del flujo.
