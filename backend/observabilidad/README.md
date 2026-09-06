# observabilidad

Pipeline de métricas del experimento. Los microservicios exportan OTLP y el
recorrido termina en un dashboard de Grafana con un panel por ASR.

```
ms-*  --OTLP http :4318-->  otel-collector  --:9464 (Prometheus exposition)-->  prometheus  -->  grafana :3000
```

Solo se levanta con el perfil `experimento`:

```sh
docker compose --profile experimento up -d
```

Y los MS solo **emiten** métricas si en `.env`:

```
OTEL_SDK_DISABLED=false
OTEL_TRACES_EXPORTER=otlp
OTEL_METRICS_EXPORTER=otlp
```

(por defecto está todo en `none` / `true` para no ensuciar los logs del modo
normal).

## Componentes

| Archivo / servicio | Rol |
|---|---|
| `otel-collector.yaml` | receiver OTLP `http` en `:4318`; processor `batch`; exporters `debug` (traces y métricas) y `prometheus` (`:9464`, solo métricas). No hay backend de trazas: los spans solo se ven en el log del collector. |
| `prometheus.yml` | un único scrape job a `otel-collector:9464` cada `5s`. |
| `grafana/provisioning/datasources/datasource.yml` | datasource Prometheus (`uid: prometheus`, `url http://prometheus:9090`, default). |
| `grafana/provisioning/dashboards/` | provider `file` + `solventa-experimento.json` (ver su README). |
| Grafana | http://localhost:3000 — acceso anónimo con rol Admin (`GF_AUTH_ANONYMOUS`), clave admin `admin`. |

## Métricas que emite `ms-perfil-riesgo` (`../DESIGN.md` §2.4)

| Métrica (nombre Prometheus) | Tipo | Labels | Uso |
|---|---|---|---|
| `solventa_profile_detection_ms` | histogram | `source_system`, `result` | ASR1 — latencia de la primera detección (umbral 700 ms) |
| `solventa_profile_retry_ms` | histogram | `source_system` | ASR3 — duración total de reintentos (presupuesto 5000 ms) |
| `solventa_profile_retry_attempts` | histogram | `source_system` | ASR3 — nº de intentos |
| `solventa_profile_cache_ms` | histogram | — | ASR2 — latencia del `GET` al caché (umbral 100 ms) |
| `solventa_profile_cache_hit_total` | counter | `hit` | ASR2 — tasa de acierto del respaldo |
| `solventa_profile_evaluation_ms` | histogram | — | latencia extremo a extremo |
| `solventa_profile_evaluation_total` | counter | `status`, `source` | resultado de cada evaluación |
| `solventa_profile_asr1_within_threshold_total` | counter | `pass` | señal directa: detección `≤ 700 ms` |
| `solventa_profile_asr2_within_threshold_total` | counter | `pass` | señal directa: caché `≤ 100 ms` |
| `solventa_profile_asr3_within_budget_total` | counter | `pass` | señal directa: retry `≤ 5000 ms` |

Los histogramas se exponen como `<nombre>_milliseconds_bucket` / `_sum` /
`_count`. Las **señales `asr{1,2,3}_within_*_total`** dan el % de cumplimiento
exacto sin depender de los buckets del histograma.

> Cada proceso hijo del pool prefork de Celery recibe su propio
> `service.instance.id` (`telemetria.py`); así el collector ve N series y los
> `sum(...)` de los dashboards agregan bien en vez de «saltar» entre workers.

## Comprobar el pipeline

```sh
curl -s http://localhost:9464/metrics | grep solventa_profile      # collector expone
curl -s 'http://localhost:9090/api/v1/query?query=solventa_profile_evaluation_total'  # prometheus tiene datos
```

## Pendiente

- `View` de OpenTelemetry para fijar buckets exactos en 700 / 100 / 5000 ms si se
  quiere un p99 «al milímetro» (hoy el % de cumplimiento ya es exacto vía los
  contadores).
- Backend de trazas (Tempo/Jaeger) si se quiere explorar spans, no solo métricas.
