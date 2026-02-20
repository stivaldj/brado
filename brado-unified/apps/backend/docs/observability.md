# Observability

## Endpoints
- `GET /metrics`: metricas em formato Prometheus.
- `GET /ready`: readiness probe.

## Metricas expostas
- `brado_http_requests_total{method,route,status_class}`
- `brado_http_request_errors_total{method,route}`
- `brado_http_request_latency_seconds_*` (histograma)

## Tracing/Correlation
- Middleware injeta `X-Trace-Id` e `traceparent` nas respostas.
- Logs JSON incluem `trace_id` e `span_id`.

## Deploy
Artefatos de monitoramento em:
- `deploy/observability/prometheus.yml`
- `deploy/observability/grafana/brado-dashboard.json`
