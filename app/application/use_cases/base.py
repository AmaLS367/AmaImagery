"""
Base classes and protocols for use cases.

Defines the contract for application use cases and their results.
"""

from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

TCommand = TypeVar("TCommand", bound="Command", contravariant=True)
TData = TypeVar("TData")


@dataclass
class Command:
    """
    Base command for use cases.

    Commands represent requests to perform business operations.
    Subclasses should define specific fields for their use case.
    """

    pass


@dataclass
class UseCaseResult(Generic[TData]):
    """
    Result of a use case execution.

    Attributes:
        success: Whether the operation succeeded
        data: Result data if successful
        error: Error message if failed
    """

    success: bool
    data: TData | None = None
    error: str | None = None


class UseCase(Protocol[TCommand, TData]):
    """
    Protocol for use case implementations.

    Use cases orchestrate business operations by coordinating between
    repositories, domain services, and external systems.
    """

    async def __call__(self, command: TCommand) -> UseCaseResult[TData]:
        """
        Execute the use case.

        Args:
            command: Command containing operation parameters

        Returns:
            UseCaseResult with success status, data, and optional error
        """
        ...
