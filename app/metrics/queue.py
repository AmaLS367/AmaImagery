"""
Metrics for task queue and worker processing.
"""

from collections.abc import Callable
from typing import Any

_make_counter: Callable[..., Any]
_make_histogram: Callable[..., Any]
_make_gauge: Callable[..., Any]

try:
    from prometheus_client import Counter as PromCounter
    from prometheus_client import Gauge as PromGauge
    from prometheus_client import Histogram as PromHistogram
except Exception:  # pragma: no cover - minimal env fallback

    class _NoopMetric:
        def labels(self, **kwargs: Any) -> "_NoopMetric":
            return self

        def inc(self, *args: Any, **kwargs: Any) -> None:
            return None

        def set(self, *args: Any, **kwargs: Any) -> None:
            return None

        def observe(self, *args: Any, **kwargs: Any) -> None:
            return None

    def _noop_counter(*args: Any, **kwargs: Any) -> _NoopMetric:
        return _NoopMetric()

    def _noop_histogram(*args: Any, **kwargs: Any) -> _NoopMetric:
        return _NoopMetric()

    def _noop_gauge(*args: Any, **kwargs: Any) -> _NoopMetric:
        return _NoopMetric()

    _make_counter = _noop_counter
    _make_histogram = _noop_histogram
    _make_gauge = _noop_gauge
else:
    _make_counter = PromCounter
    _make_histogram = PromHistogram
    _make_gauge = PromGauge


# Queue metrics
queue_size = _make_gauge(
    "queue_size",
    "Current number of tasks in the queue",
    ["queue_name"],
)

queue_enqueued_total = _make_counter(
    "queue_enqueued_total",
    "Total number of tasks enqueued",
    ["queue_name"],
)

queue_dequeued_total = _make_counter(
    "queue_dequeued_total",
    "Total number of tasks dequeued",
    ["queue_name"],
)

# Worker processing metrics
worker_task_duration_seconds = _make_histogram(
    "worker_task_duration_seconds",
    "Time spent processing tasks in workers",
    ["queue_name", "task_type"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
)

worker_task_status_total = _make_counter(
    "worker_task_status_total",
    "Total number of tasks by status",
    ["queue_name", "task_type", "status"],
)

worker_task_errors_total = _make_counter(
    "worker_task_errors_total",
    "Total number of task processing errors",
    ["queue_name", "task_type", "error_type"],
)


def record_queue_enqueue(queue_name: str = "generation") -> None:
    """
    Records that a task has been enqueued.
    """
    queue_enqueued_total.labels(queue_name=queue_name).inc()


def record_queue_dequeue(queue_name: str = "generation") -> None:
    """
    Records that a task has been dequeued.
    """
    queue_dequeued_total.labels(queue_name=queue_name).inc()


def update_queue_size(queue_name: str, size: int) -> None:
    """
    Updates the current queue size.
    """
    queue_size.labels(queue_name=queue_name).set(size)


def record_task_start(queue_name: str = "generation", task_type: str = "image_generation") -> None:
    """
    Records that a task has started processing.
    """
    worker_task_status_total.labels(queue_name=queue_name, task_type=task_type, status="started").inc()


def record_task_success(
    queue_name: str = "generation",
    task_type: str = "image_generation",
    duration_seconds: float = 0.0,
) -> None:
    """
    Records a successful task completion with duration.
    """
    worker_task_status_total.labels(queue_name=queue_name, task_type=task_type, status="success").inc()
    worker_task_duration_seconds.labels(queue_name=queue_name, task_type=task_type).observe(duration_seconds)


def record_task_error(
    queue_name: str = "generation",
    task_type: str = "image_generation",
    error_type: str = "unknown",
) -> None:
    """
    Records a task processing error.
    """
    worker_task_status_total.labels(queue_name=queue_name, task_type=task_type, status="error").inc()
    worker_task_errors_total.labels(queue_name=queue_name, task_type=task_type, error_type=error_type).inc()
