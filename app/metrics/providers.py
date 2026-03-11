"""
Metrics for image generation providers.
"""

try:
    from prometheus_client import Counter, Histogram
except Exception:  # pragma: no cover - minimal env fallback

    class _NoopMetric:
        def labels(self, **kwargs):
            return self

        def inc(self, *args, **kwargs):
            return None

        def observe(self, *args, **kwargs):
            return None

    def Counter(*args, **kwargs):
        return _NoopMetric()

    def Histogram(*args, **kwargs):
        return _NoopMetric()


# Provider generation metrics
provider_generation_total = Counter(
    "provider_generation_total",
    "Total number of generation requests",
    ["provider_name", "status"],
)

provider_generation_duration_seconds = Histogram(
    "provider_generation_duration_seconds",
    "Time spent generating images",
    ["provider_name"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0],
)

provider_generation_errors_total = Counter(
    "provider_generation_errors_total",
    "Total number of generation errors",
    ["provider_name", "error_type"],
)


def record_generation_start(provider_name: str) -> None:
    """
    Records that a generation request has started.
    """
    provider_generation_total.labels(provider_name=provider_name, status="started").inc()


def record_generation_success(provider_name: str, duration_seconds: float) -> None:
    """
    Records a successful generation with duration.
    """
    provider_generation_total.labels(provider_name=provider_name, status="success").inc()
    provider_generation_duration_seconds.labels(provider_name=provider_name).observe(duration_seconds)


def record_generation_error(provider_name: str, error_type: str) -> None:
    """
    Records a generation error.
    """
    provider_generation_total.labels(provider_name=provider_name, status="error").inc()
    provider_generation_errors_total.labels(provider_name=provider_name, error_type=error_type).inc()
