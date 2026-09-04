# dashboards

`solventa-experimento.json` — dashboard único, provisionado automáticamente
por Grafana. Organizado en rows:

- **Resumen del experimento**: tasa de éxito global, errores no controlados
  (`status=DEGRADED_NO_FALLBACK`, debe quedarse en 0), resultado por
  `status`/`source` y tasa de resultados en el tiempo.
- **ASR1 / ASR2 / ASR3**: un row por ASR, cada uno con la línea de umbral
  (700 / 100 / 5000 ms), p95 vía `histogram_quantile(...)` sobre
  `solventa_profile_*_ms_milliseconds_bucket`, y la tasa de cumplimiento vía
  `solventa_profile_asr{1,2,3}_within_*_total{pass="true"}` (no depende de los
  buckets del histograma, es una señal directa).
- **Latencia end-to-end**: p50/p95 de `solventa_profile_evaluation_ms`.

No hay variable de escenario (esa etiqueta no existe en las métricas de este
repo): los paneles se filtran por las etiquetas reales que emite
`ms-perfil-riesgo` (`source_system`, `status`, `source`, `pass`, `hit`).
