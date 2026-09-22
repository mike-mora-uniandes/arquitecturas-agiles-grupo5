# experimento

Scripts que materializan los dos ataques del experimento — **no son
servicios de `docker-compose`**, se ejecutan manualmente contra el stack ya
levantado, igual que se hizo con las pruebas manuales del experimento 1.

| Script | Escenario | ASR |
|---|---|---|
| `forjar_token.py` | Confidencialidad — token de sesión forjado con PyJWT, extracción no autorizada del perfil de otro cliente | ASR1 / ASR3 |
| `mitm_alterar_perfil.py` | Integridad — addon de mitmproxy que altera el perfil en tránsito entre `ms-cliente` y `ms-riesgo` | ASR2 / ASR4 |

Pendiente:
- Implementar ambos scripts (hoy son plantillas con `TODO`/`NotImplementedError`).
- Documentar aquí el paso a paso exacto de cada corrida (equivalente a la
  sección "Ejecutar el experimento" del README raíz de `backend/`), una vez
  que `ms-identidad`/`ms-cliente`/`ms-riesgo` tengan lógica real.
- Capturar y guardar evidencia de cada corrida (tiempos de detección/notificación).
