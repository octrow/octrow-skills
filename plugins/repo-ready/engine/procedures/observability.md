# Metrics and traces: OpenTelemetry and Prometheus

Worked through on octrow/buy-smarter (`src/buysmarter/telemetry.py`, `deploy/observability/`).

## Instrumentation

1. Domain instruments on the global meter at module level; in a CLI without a provider they are no-ops.
2. One `instrument_app(app)`: a MeterProvider with `PrometheusMetricReader`, `GET /metrics` as a route
   (`generate_latest()`), FastAPI / httpx / SQLAlchemy instrumentation, OTLP traces only when
   `OTEL_EXPORTER_OTLP_ENDPOINT` is set, and an off switch (`<APP>_METRICS=0`).
3. Metrics are recorded in the service layer (around the main function, at calls to external sources, in the LLM
   adapter), not in the CLI.
4. A test helper parses `/metrics` with `prometheus_client.parser` and checks that a counter went up.

## Labels

Low-cardinality labels only: outcome, source, model. Never free text such as the user's query: every distinct value
is a new time series and the metrics backend runs out of memory.

## Probes out of the metrics

Exclude the probes and the metrics endpoint itself from HTTP instrumentation (`excluded_urls="health,ready,metrics"`).
Kubernetes calls them every few seconds, and they drown the real latency.

## Dashboards

A Compose profile with Prometheus, Grafana (provisioned datasource and dashboard) and Jaeger v2 (it takes OTLP
itself; no collector while there is one backend). An empty panel: `or vector(0)` plus `axisSoftMax: 1`, and a label
for the zero series via `label_replace`; don't draw a ratio with a zero denominator as zero, switch the panel to a
counter.

## Pitfalls

- `OTEL_SEMCONV_STABILITY_OPT_IN=http` (stable names only; `http/dup` emits old and new side by side while
  dashboards migrate) is read once by the first instrumentor. If another one (taskiq) is imported
  earlier, the old conventions win and `http_route` disappears: `os.environ.setdefault` it at the top of the
  telemetry module.
- After moving work to a worker, its metrics live there: the worker serves its own `/metrics` on another port.
