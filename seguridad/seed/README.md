# seed

Servicio one-shot (`docker compose up` lo corre y termina) que puebla con
datos dummy generados con **Faker** las bases PostgreSQL de `ms-identidad`
(`GestiónRoles`) y `ms-riesgo` (`PerfilRiesgo`). No compartido con
`ms-audit` — esa base empieza vacía, se llena con la propia corrida del
experimento.

Pendiente:
- Conexión real a las 3 bases (`psycopg2`) y `INSERT` de los registros
  generados con Faker.
- Definir el número y perfil de clientes dummy necesarios para los 2
  escenarios de ataque (confidencialidad e integridad).
