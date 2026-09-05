# Dashboards

`solventa-experimento.json` — **«Solventa - Experimento de disponibilidad
(PerfilRiesgo)»**. Dashboard único, provisionado automáticamente (provider `file`
en `dashboards.yml`). Datasource: Prometheus `uid: prometheus`.

Organizado en filas:

## Resumen del experimento
- **Tasa de éxito global** —
  `100 * (sum(status="OK") + sum(status="DEGRADED", source="CACHE")) / sum(total)`.
  Cuenta como éxito la respuesta en vivo **y** la degradada con respaldo; deja
  fuera `DEGRADED_NO_FALLBACK`.
- **Errores no controlados hacia el analista** — recuento de
  `status="DEGRADED_NO_FALLBACK"`; debe quedarse en **0** salvo el caso de prueba
  `C006` (cache miss deliberado).
- **Resultado por status / source** — `sum by (status, source)`.
- **Tasa de resultados en el tiempo** — `rate(...[1m])` por `status`.

## ASR1 — Exception Detection (< 700 ms)
- **P99 del tiempo de detección por fuente externa** —
  `histogram_quantile(0.99, ... rate(solventa_profile_detection_ms_milliseconds_bucket[5m]) ...)`
  con línea de umbral en 700 ms.
- **% de detecciones que cumplen ASR1 (≤ 700 ms)** —
  `solventa_profile_asr1_within_threshold_total{pass="true"}`.

## ASR2 — Exception Handling vía caché Redis (< 100 ms)
- **P99 del tiempo de respuesta del caché** — sobre
  `solventa_profile_cache_ms_milliseconds_bucket`, umbral 100 ms.
- **% de consultas al caché que cumplen ASR2 (≤ 100 ms)** —
  `solventa_profile_asr2_within_threshold_total{pass="true"}`.
- **Tasa de cache hit** — `solventa_profile_cache_hit_total{hit="true"}`.

## ASR3 — Retry (≤ 3 intentos, backoff exponencial, ≤ 5 s totales)
- **P99 de la duración total de reintentos por fuente** — sobre
  `solventa_profile_retry_ms_milliseconds_bucket`, umbral 5000 ms.
- **Promedio de intentos por reintento** —
  `rate(solventa_profile_retry_attempts_sum[5m]) / rate(..._count[5m])`.
- **% de ventanas de retry que cumplen ASR3 (≤ 5000 ms)** —
  `solventa_profile_asr3_within_budget_total{pass="true"}`.

## Latencia end-to-end del flujo de evaluación
- **P50 / P99** de `solventa_profile_evaluation_ms` (sin umbral fijado en el
  cuaderno; se observa como referencia).

---

No hay variable de «escenario»: esa etiqueta no existe en las métricas de este
repo. Los paneles se filtran por las labels reales que emite `ms-perfil-riesgo`
(`source_system`, `status`, `source`, `pass`, `hit`). Para atribuir resultados a
un `customer_id` concreto hay que cruzar con las trazas / logs, no con estas
métricas.

`allowUiUpdates: true`: se puede editar en la UI, pero para persistir hay que
volcar el JSON aquí.
