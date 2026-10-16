"""Observability stack pack: metrics and traces (judged by reading the code)."""
from registry import judgement

DEP = {"deploy"}

judgement("metrics_low_cardinality", severity="warning", when=("metrics",), scenarios=DEP,
          question="Are metric labels low-cardinality only (outcome, source, model), never free text such as a "
                   "user's query?",
          procedure="observability.md#labels")

judgement("metrics_probes_excluded", severity="info", when=("metrics",), scenarios=DEP,
          question="Are /health, /ready and /metrics excluded from HTTP instrumentation?",
          procedure="observability.md#probes-out-of-the-metrics")

judgement("metrics_in_service_layer", severity="info", when=("metrics",), scenarios=DEP,
          question="Is there one `instrument_app` (metrics route, OTLP only when its endpoint is set, an off "
                   "switch), with metrics recorded in the service layer rather than the CLI?",
          procedure="observability.md#instrumentation")
