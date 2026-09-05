"""Prometheus metrics instrumentation for the FastAPI triage service."""

from prometheus_client import Counter, Histogram

# ---------------------------------------------------------------------------
# Counters
# ---------------------------------------------------------------------------
REQUEST_COUNT = Counter(
    name="triage_api_requests_total",
    documentation="Total number of requests received by the API",
    labelnames=["method", "endpoint", "http_status"],
)

PREDICTION_COUNT = Counter(
    name="triage_api_predictions_total",
    documentation="Total number of predictions made, broken down by predicted label",
    labelnames=["predicted_label"],
)

ERROR_COUNT = Counter(
    name="triage_api_errors_total",
    documentation="Total number of prediction errors (5xx responses)",
    labelnames=["endpoint"],
)

# ---------------------------------------------------------------------------
# Histograms
# ---------------------------------------------------------------------------
REQUEST_LATENCY = Histogram(
    name="triage_api_request_duration_seconds",
    documentation="Latency of HTTP requests in seconds",
    labelnames=["method", "endpoint"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)

PREDICTION_LATENCY = Histogram(
    name="triage_api_prediction_duration_seconds",
    documentation="Latency of model inference in seconds",
    buckets=(0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05, 0.1, 0.5),
)
