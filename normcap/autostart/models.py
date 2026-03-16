"""Data models for the autostart module."""

import enum
from typing import Protocol


class HandlerProtocol(Protocol):
    """Interface for autostart handler modules."""

    install_instructions: str

    def enable(self) -> bool:
        """Enable autostart. Returns ``True`` on success."""
        ...  # pragma: no cover

    def disable(self) -> None:
        """Disable autostart."""
        ...  # pragma: no cover

    def is_enabled(self) -> bool:
        """Return ``True`` if autostart is currently active."""
        ...  # pragma: no cover

    def is_compatible(self) -> bool:
        """Return ``True`` if this handler supports the current platform."""
        ...  # pragma: no cover

    def is_installed(self) -> bool:
        """Return ``True`` if all required dependencies are available."""
        ...  # pragma: no cover


class Handler(enum.IntEnum):
    """Supported autostart handlers, ordered by preference."""

    WINDOWS = enum.auto()
