# observabilidad

Pipeline base para el experimento: los microservicios exportan OTLP →
`otel-collector` → `prometheus` → `grafana`.

```
ms-* --(OTLP http :4318)--> otel-collector --(:9464)--> prometheus --> grafana
```

Se levanta con `docker compose --profile experimento up`. Para que los MS
**emitan** métricas hay que poner `OTEL_SDK_DISABLED=false` en `.env`
(por defecto está en `true` para no ensuciar logs en el modo normal).

- `otel-collector.yaml` — receiver OTLP + exporters `debug` y `prometheus`.
- `prometheus.yml` — scrapea `otel-collector:9464` cada 5 s.
- `grafana/provisioning/datasources/` — datasource Prometheus (uid fijo `prometheus`, anónimo, admin).
- `grafana/provisioning/dashboards/` — `solventa-experimento.json`: resumen + un row por ASR.

## Métricas que expone MS PerfilRiesgo (DESIGN.md §2.4)

| Métrica | Uso |
|---|---|
| `solventa_profile_detection_ms` | latencia de detección (ASR1, umbral 700) |
| `solventa_profile_retry_ms` / `_attempts` | reintentos (ASR3, presupuesto 5000) |
| `solventa_profile_cache_ms` | latencia del caché (ASR2, umbral 100) |
| `solventa_profile_evaluation_ms` / `_total` | extremo a extremo, por `status`/`source` |
| `solventa_profile_asr1_within_threshold_total` | señal directa de cumplimiento ASR1 |
| `solventa_profile_asr2_within_threshold_total` | señal directa de cumplimiento ASR2 |
| `solventa_profile_asr3_within_budget_total` | señal directa de cumplimiento ASR3 |

## Pendiente

- Ajustar buckets de histograma con una `View` si se necesita un límite exacto
  en 700 ms para el p95 (hoy el % de cumplimiento ya es exacto vía los
  contadores `asr{1,2,3}_*_total`, que no dependen del bucket).
