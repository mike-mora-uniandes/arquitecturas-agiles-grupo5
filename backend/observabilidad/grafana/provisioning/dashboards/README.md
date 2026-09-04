# dashboards

Pendiente (responsable de observabilidad). Coloca aquí los `.json` de los
dashboards; Grafana los carga automáticamente.

Un panel por ASR con:
- la línea de umbral (700 / 100 / 5000 ms),
- p95 / p99 vía `histogram_quantile(...)` sobre `solventa_profile_*_ms_bucket`,
- la tasa de cumplimiento vía `solventa_profile_asr{1,2,3}_within_*_total{pass="true"}`.

Más un panel de criterio global: `sum by (status) (rate(solventa_profile_evaluation_total[1m]))`
(debe ser 0 en cualquier `status` de error no controlado).
