"""Dispatcher for registering global hotkeys across platforms."""

import logging
from collections.abc import Callable

from PySide6 import QtWidgets

from normcap.hotkey.handlers import windows
from normcap.hotkey.models import Handler, HandlerProtocol

logger = logging.getLogger(__name__)

_hotkey_handlers: dict[Handler, HandlerProtocol] = {
    Handler.WINDOWS: windows,
}

_active_handler: Handler | None = None


def _register(
    hotkey: str,
    handler: Handler,
    app: QtWidgets.QApplication,
    callback: Callable[[], None],
) -> bool:
    hotkey_handler = _hotkey_handlers[handler]
    try:
        return hotkey_handler.register(hotkey=hotkey, app=app, callback=callback)
    except Exception:
        logger.exception("%s's register() failed!", handler.name)
        return False


def _unregister(handler: Handler, app: QtWidgets.QApplication) -> None:
    hotkey_handler = _hotkey_handlers[handler]
    try:
        hotkey_handler.unregister(app=app)
    except Exception:
        logger.exception("%s's unregister() failed!", handler.name)


def register(
    hotkey: str,
    app: QtWidgets.QApplication,
    callback: Callable[[], None],
) -> bool:
    """Register a global hotkey using the first compatible handler.

    Args:
        hotkey: Hotkey string in lowercase-plus format, e.g. ``"ctrl+shift+j"``.
        app: The running ``QApplication`` instance.
        callback: Function to call when the hotkey is triggered.

    Returns:
        ``True`` if at least one handler succeeded, ``False`` otherwise.
    """
    global _active_handler  # noqa: PLW0603

    # Try new handlers before unregistering the current one; only swap on success.
    for handler in get_available_handlers():
        if _register(hotkey=hotkey, handler=handler, app=app, callback=callback):
            if _active_handler is not None and _active_handler is not handler:
                _unregister(handler=_active_handler, app=app)
            _active_handler = handler
            return True

    logger.error("Unable to register hotkey! (Increase log-level for details)")
    return False


def unregister(app: QtWidgets.QApplication) -> None:
    """Unregister any previously registered global hotkey.

    Args:
        app: The running ``QApplication`` instance.
    """
    global _active_handler  # noqa: PLW0603

    if _active_handler is not None:
        _unregister(handler=_active_handler, app=app)
        _active_handler = None


def get_available_handlers() -> list[Handler]:
    """Return a list of compatible and installed hotkey handlers.

    Returns:
        Ordered list of handlers that are both compatible with this platform
        and have all required dependencies available.
    """
    compatible_handlers = [
        h for h in Handler if _hotkey_handlers[h].is_compatible()
    ]
    logger.debug(
        "Compatible hotkey handlers: %s", [h.name for h in compatible_handlers]
    )

    if not compatible_handlers:
        logger.debug(
            "None of the implemented hotkey handlers is compatible with this system"
        )
        return []

    available_handlers = [
        h for h in compatible_handlers if _hotkey_handlers[h].is_installed()
    ]
    logger.debug(
        "Available hotkey handlers: %s", [h.name for h in available_handlers]
    )

    if not available_handlers:
        logger.error(
            "No working hotkey handler found for your system. "
            "The preferred handler on your system would be %s but can't be "
            "used due to missing dependencies. %s",
            compatible_handlers[0].name,
            _hotkey_handlers[compatible_handlers[0]].install_instructions,
        )
        return []

    return available_handlers
