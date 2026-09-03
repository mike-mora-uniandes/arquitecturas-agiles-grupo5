# observabilidad

OpenTelemetry (qué medir y dónde) + visualización en Grafana según los ASRs y
la hipótesis del experimento.

Pendiente:
- `otel-collector.yaml` (recepción OTLP desde los 3 microservicios),
- `grafana/` con provisioning y dashboards (latencia de detección ASR1,
  tiempo de respuesta desde caché ASR2, duración/nº de reintentos ASR3),
- servicios `otel-collector` y `grafana` en `docker-compose.yml`,
- instrumentación OTel en `ms-*/telemetria.py`.
