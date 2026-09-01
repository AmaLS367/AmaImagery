"""
Metrics for image generation providers.
"""

from collections.abc import Callable
from typing import Any

_make_counter: Callable[..., Any]
_make_histogram: Callable[..., Any]

try:
    from prometheus_client import Counter as PromCounter
    from prometheus_client import Histogram as PromHistogram
except Exception:  # pragma: no cover - minimal env fallback

    class _NoopMetric:
        def labels(self, **kwargs: Any) -> "_NoopMetric":
            return self

        def inc(self, *args: Any, **kwargs: Any) -> None:
            return None

        def observe(self, *args: Any, **kwargs: Any) -> None:
            return None

    def _noop_counter(*args: Any, **kwargs: Any) -> _NoopMetric:
        return _NoopMetric()

    def _noop_histogram(*args: Any, **kwargs: Any) -> _NoopMetric:
        return _NoopMetric()

    _make_counter = _noop_counter
    _make_histogram = _noop_histogram
else:
    _make_counter = PromCounter
    _make_histogram = PromHistogram


# Provider generation metrics
provider_generation_total = _make_counter(
    "provider_generation_total",
    "Total number of generation requests",
    ["provider_name", "status"],
)

provider_generation_duration_seconds = _make_histogram(
    "provider_generation_duration_seconds",
    "Time spent generating images",
    ["provider_name"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0],
)

provider_generation_errors_total = _make_counter(
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
