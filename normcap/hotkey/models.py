"""Data models for the hotkey module."""

import enum
from collections.abc import Callable
from typing import Protocol

from PySide6 import QtWidgets


class HandlerProtocol(Protocol):
    """Protocol that all hotkey handler modules must implement."""

    install_instructions: str

    def register(
        self,
        hotkey: str,
        app: QtWidgets.QApplication,
        callback: Callable[[], None],
    ) -> bool:
        """Register a global hotkey.

        Args:
            hotkey: Hotkey string in lowercase-plus format, e.g. ``"ctrl+shift+j"``.
            app: The running ``QApplication`` instance.
            callback: Function to call when the hotkey is triggered.

        Returns:
            ``True`` if registration succeeded, ``False`` otherwise.
        """
        ...  # pragma: no cover

    def unregister(self, app: QtWidgets.QApplication) -> None:
        """Unregister the previously registered global hotkey.

        Args:
            app: The running ``QApplication`` instance.
        """
        ...  # pragma: no cover

    def is_compatible(self) -> bool:
        """Check whether this handler is compatible with the current platform.

        Returns:
            ``True`` if the system could use this handler.
        """
        ...  # pragma: no cover

    def is_installed(self) -> bool:
        """Check whether all runtime dependencies are available.

        Returns:
            ``True`` if all necessary dependencies are present.
        """
        ...  # pragma: no cover


class Handler(enum.IntEnum):
    """All supported hotkey handlers.

    The handlers are ordered by preference: ``register()`` tries them from top
    to bottom and uses the first one detected as compatible.
    """

    # For win32
    WINDOWS = enum.auto()
