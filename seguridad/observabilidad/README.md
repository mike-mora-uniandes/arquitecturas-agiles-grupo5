# observabilidad

Pipeline de métricas del experimento de seguridad, mismo patrón que
`../../backend/observabilidad/` (experimento 1): los microservicios emiten OTLP
al **OpenTelemetry Collector**, que las expone a **Prometheus**, y **Grafana**
las grafica contra los umbrales de los ASR.

```
ms-audit / ms-notificaciones ─OTLP/http→ otel-collector ─/metrics→ prometheus ─datasource→ grafana
```

Solo se levantan con el perfil `experimento`:

```sh
# emitir métricas: en .env poner OTEL_SDK_DISABLED=false y *_EXPORTER=otlp
docker compose --profile experimento up -d --build
```

## Puertos de host (distintos al experimento 1 para correr ambos a la vez)

| Servicio | Host | Experimento 1 |
|---|---|---|
| Grafana | http://localhost:3001 | 3000 |
| Prometheus | http://localhost:9091 | 9090 |
| OTel Collector (OTLP http) | 4319 | 4318 |
| OTel Collector (`/metrics`) | 9465 | 9464 |

Entre contenedores el endpoint sigue siendo `http://otel-collector:4318` (el
remapeo de host no afecta la red interna).

## Archivos

| Archivo | Rol |
|---|---|
| `otel-collector.yaml` | recibe OTLP, exporta a Prometheus (`:9464`) |
| `prometheus.yml` | scrapea `otel-collector:9464` cada 5 s |
| `grafana/provisioning/datasources/datasource.yml` | datasource Prometheus (uid `prometheus`) |
| `grafana/provisioning/dashboards/dashboards.yml` | provisioning del dashboard |
| `grafana/provisioning/dashboards/solventa-seguridad.json` | **dashboard del experimento** |

## Dashboard — *Solventa · Experimento de seguridad*

| Fila | Panel | Query base |
|---|---|---|
| Resumen | Intrusiones detectadas / por tipo | `solventa_seguridad_intrusiones_total` |
| ASR1 | P99 detección confidencialidad vs. 200 ms · % cumple | `tiempo_deteccion_confidencialidad_ms_milliseconds_bucket` · `..._asr1_within_threshold_total` |
| ASR2 | P99 detección integridad vs. 500 ms · % cumple | `tiempo_deteccion_integridad_ms_milliseconds_bucket` · `..._asr2_within_threshold_total` |
| ASR3/4 | P99 notificación vs. 5 s (por tipo) · % cumple | `tiempo_notificacion_ms_milliseconds_bucket` · `..._asr_notificacion_within_total` |

> El exporter de Prometheus añade el sufijo `_milliseconds` al nombre de los
> histogramas cuya unidad es `ms` (por eso las series se llaman
> `tiempo_*_ms_milliseconds_bucket`), igual que en el experimento 1.
