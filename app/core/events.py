"""
Domain event bus for publishing and handling domain events.
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DomainEvent:
    """
    Base class for domain events.

    All domain events must have a name, timestamp, and payload.
    """

    name: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class ImageGeneratedEvent(DomainEvent):
    """
    Event published when an image is successfully generated.
    """

    def __init__(self, task_id: str, user_id: str, image_path: str, metadata: dict[str, Any]):
        super().__init__(
            name="image_generated",
            payload={
                "task_id": task_id,
                "user_id": user_id,
                "image_path": image_path,
                "metadata": metadata,
            },
        )


@dataclass
class GenerationFailedEvent(DomainEvent):
    """
    Event published when image generation fails.
    """

    def __init__(self, task_id: str, user_id: str, error: str, error_type: str | None = None):
        super().__init__(
            name="generation_failed",
            payload={
                "task_id": task_id,
                "user_id": user_id,
                "error": error,
                "error_type": error_type,
            },
        )


EventHandler = Callable[[DomainEvent], None]
AsyncEventHandler = Callable[[DomainEvent], Awaitable[None]]
EventHandleType = EventHandler | AsyncEventHandler


class EventBus:
    """
    Simple event bus for publishing and handling domain events.

    Supports both sync and async event handlers.
    Handlers are called in the order they were registered.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandleType]] = {}

    def subscribe(self, event_name: str, handler: EventHandleType) -> None:
        """
        Register an event handler for a specific event type.

        Args:
            event_name: Name of the event to subscribe to
            handler: Function to call when event is published (sync or async)
        """
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append(handler)

    def unsubscribe(self, event_name: str, handler: EventHandleType) -> None:
        """
        Unregister an event handler.

        Args:
            event_name: Name of the event
            handler: Handler to remove
        """
        if event_name in self._handlers:
            try:
                self._handlers[event_name].remove(handler)
            except ValueError:
                pass

    async def publish(self, event: DomainEvent) -> None:
        """
        Publish a domain event to all registered handlers.

        Args:
            event: Domain event to publish
        """
        handlers = self._handlers.get(event.name, [])

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as exc:
                logger.warning("event_handler_failed", extra={"event_name": event.name, "error": str(exc)})


_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """
    Returns singleton EventBus instance.
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
