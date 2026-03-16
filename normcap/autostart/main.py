"""Dispatcher for enabling/disabling autostart across platforms."""

import logging

from normcap.autostart.handlers import windows
from normcap.autostart.models import Handler, HandlerProtocol

logger = logging.getLogger(__name__)

_autostart_handlers: dict[Handler, HandlerProtocol] = {
    Handler.WINDOWS: windows,
}


def _enable(handler: Handler) -> bool:
    autostart_handler = _autostart_handlers[handler]
    try:
        return autostart_handler.enable()
    except Exception:
        logger.exception("%s's enable() failed!", handler.name)
        return False


def _disable(handler: Handler) -> None:
    autostart_handler = _autostart_handlers[handler]
    try:
        autostart_handler.disable()
    except Exception:
        logger.exception("%s's disable() failed!", handler.name)


def _is_enabled(handler: Handler) -> bool:
    autostart_handler = _autostart_handlers[handler]
    try:
        return autostart_handler.is_enabled()
    except Exception:
        logger.exception("%s's is_enabled() failed!", handler.name)
        return False


def enable() -> bool:
    """Enable autostart via the first compatible handler.

    Returns:
        ``True`` if at least one handler succeeded, ``False`` otherwise.
    """
    any_handler = False
    for handler in get_available_handlers():
        any_handler = True
        if _enable(handler):
            return True

    if not any_handler:
        logger.debug("No compatible autostart handler found; skipping enable.")
    else:
        logger.warning(
            "Autostart could not be enabled: all available autostart handlers failed."
        )
    return False


def disable() -> None:
    """Disable autostart on all compatible handlers."""
    any_handler = False
    for handler in get_available_handlers():
        any_handler = True
        _disable(handler)

    if not any_handler:
        logger.debug("No compatible autostart handler found; skipping disable.")


def is_enabled() -> bool:
    """Return ``True`` if any handler reports autostart as active."""
    return any(_is_enabled(handler) for handler in get_available_handlers())


def get_available_handlers() -> list[Handler]:
    """Return compatible and installed autostart handlers."""
    compatible_handlers = [h for h in Handler if _autostart_handlers[h].is_compatible()]
    logger.debug(
        "Compatible autostart handlers: %s", [h.name for h in compatible_handlers]
    )

    if not compatible_handlers:
        logger.debug(
            "None of the implemented autostart handlers is compatible with this system"
        )
        return []

    available_handlers = [
        h for h in compatible_handlers if _autostart_handlers[h].is_installed()
    ]
    logger.debug(
        "Available autostart handlers: %s", [h.name for h in available_handlers]
    )

    if not available_handlers:
        logger.error(
            "No working autostart handler found for your system. "
            "The preferred handler on your system would be %s but can't be "
            "used due to missing dependencies. %s",
            compatible_handlers[0].name,
            _autostart_handlers[compatible_handlers[0]].install_instructions,
        )
        return []

    return available_handlers
