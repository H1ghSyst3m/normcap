"""Windows global hotkey handler using RegisterHotKey + WM_HOTKEY."""

import ctypes
import logging
import sys
from collections.abc import Callable

from PySide6 import QtCore, QtWidgets

logger = logging.getLogger(__name__)

install_instructions = ""  # ctypes is stdlib, pre-installed on Windows

_WM_HOTKEY = 0x0312
_HOTKEY_ID = 1

# Win32 modifier flags
_MOD_ALT = 0x0001
_MOD_CONTROL = 0x0002
_MOD_SHIFT = 0x0004
_MOD_WIN = 0x0008
_MOD_NOREPEAT = 0x4000

_MODIFIER_MAP: dict[str, int] = {
    "alt": _MOD_ALT,
    "ctrl": _MOD_CONTROL,
    "control": _MOD_CONTROL,
    "shift": _MOD_SHIFT,
    "win": _MOD_WIN,
    "meta": _MOD_WIN,
}

_VK_MAP: dict[str, int] = {
    "space": 0x20,
    "enter": 0x0D,
    "return": 0x0D,
    "backspace": 0x08,
    "tab": 0x09,
    "esc": 0x1B,
    "escape": 0x1B,
    "delete": 0x2E,
    "del": 0x2E,
    "insert": 0x2D,
    "ins": 0x2D,
    "home": 0x24,
    "end": 0x23,
    "pageup": 0x21,
    "pgup": 0x21,
    "pagedown": 0x22,
    "pgdn": 0x22,
    "left": 0x25,
    "up": 0x26,
    "right": 0x27,
    "down": 0x28,
    "f1": 0x70,
    "f2": 0x71,
    "f3": 0x72,
    "f4": 0x73,
    "f5": 0x74,
    "f6": 0x75,
    "f7": 0x76,
    "f8": 0x77,
    "f9": 0x78,
    "f10": 0x79,
    "f11": 0x7A,
    "f12": 0x7B,
    # Qt PortableText punctuation tokens (QKeySequence serialises symbols by name)
    "plus": 0xBB,
    "equal": 0xBB,
    "minus": 0xBD,
    "semicolon": 0xBA,
    "comma": 0xBC,
    "period": 0xBE,
    "slash": 0xBF,
    "quoteleft": 0xC0,
    "bracketleft": 0xDB,
    "backslash": 0xDC,
    "bracketright": 0xDD,
    "apostrophe": 0xDE,
}


def parse_hotkey(hotkey: str) -> tuple[int, int]:
    """Parse a hotkey string into Win32 modifier flags and virtual key code.

    Args:
        hotkey: Hotkey string in lowercase-plus format, e.g. ``"ctrl+shift+j"``.

    Returns:
        A ``(modifiers, vk)`` tuple suitable for ``RegisterHotKey``.

    Raises:
        ValueError: If the hotkey string is empty, contains an unknown token, or
            has no non-modifier key (or more than one).
    """
    parts = [p.strip().lower() for p in hotkey.split("+")]
    if not parts or parts == [""]:
        raise ValueError(f"Invalid hotkey string: {hotkey!r}")

    modifiers = 0
    vk: int | None = None

    for part in parts:
        if not part:
            raise ValueError(f"Invalid hotkey string: {hotkey!r}")
        if part in _MODIFIER_MAP:
            modifiers |= _MODIFIER_MAP[part]
        elif part in _VK_MAP:
            if vk is not None:
                raise ValueError(f"Multiple non-modifier keys in hotkey: {hotkey!r}")
            vk = _VK_MAP[part]
        elif len(part) == 1:
            if vk is not None:
                raise ValueError(f"Multiple non-modifier keys in hotkey: {hotkey!r}")
            vk = ord(part.upper())
        else:
            raise ValueError(f"Unknown key token: {part!r}")

    if vk is None:
        raise ValueError(f"No non-modifier key found in hotkey: {hotkey!r}")

    return modifiers, vk


class _WindowsNativeEventFilter(QtCore.QAbstractNativeEventFilter):
    """Native event filter that forwards ``WM_HOTKEY`` messages to a callback."""

    def __init__(self, hotkey_id: int, callback: Callable[[], None]) -> None:
        super().__init__()
        self._hotkey_id = hotkey_id
        self._callback = callback

    def nativeEventFilter(  # noqa: N802
        self, event_type: bytes, message: object
    ) -> tuple[bool, int]:
        if event_type in (b"windows_generic_MSG", b"windows_dispatcher_MSG"):
            import ctypes.wintypes  # only available on Windows

            try:
                msg = ctypes.wintypes.MSG.from_address(int(message))  # type: ignore[call-overload]
            except (TypeError, ValueError):
                return False, 0
            if msg.message == _WM_HOTKEY and msg.wParam == self._hotkey_id:
                logger.debug("WM_HOTKEY received (id=%s)", self._hotkey_id)
                self._callback()
                return True, 0
        return False, 0


# Module-level filter instance; kept alive so Qt does not GC it.
_filter: _WindowsNativeEventFilter | None = None
# Hotkey string and callback that are currently registered with the OS.
_active_hotkey: str | None = None
_active_callback: Callable[[], None] | None = None


def register(
    hotkey: str,
    app: QtWidgets.QApplication,
    callback: Callable[[], None],
) -> bool:
    """Register a global hotkey via ``RegisterHotKey``.

    Args:
        hotkey: Hotkey string in lowercase-plus format, e.g. ``"ctrl+shift+j"``.
        app: The running ``QApplication`` instance.
        callback: Function to call when the hotkey is triggered.

    Returns:
        ``True`` if registration succeeded, ``False`` otherwise.
    """
    global _filter, _active_hotkey, _active_callback  # noqa: PLW0603

    if not hotkey:
        logger.debug("Empty hotkey string, skipping registration")
        return False

    # Validate first to preserve existing registration on parse errors.
    try:
        modifiers, vk = parse_hotkey(hotkey)
    except ValueError:
        logger.exception("Failed to parse hotkey %r", hotkey)
        return False

    # Save old state for rollback in case the OS call fails.
    prev_hotkey = _active_hotkey
    prev_callback = _active_callback

    # Only unregister once we know the new hotkey is valid.
    unregister(app)

    result = ctypes.windll.user32.RegisterHotKey(  # type: ignore[attr-defined]
        None, _HOTKEY_ID, modifiers | _MOD_NOREPEAT, vk
    )
    if not result:
        error_code = ctypes.GetLastError()  # type: ignore[attr-defined]
        logger.error("RegisterHotKey failed for %r (error=%s)", hotkey, error_code)
        # Attempt to restore the previous registration so callers can rely on
        # a False return meaning "new hotkey failed, old one still active".
        if prev_hotkey is not None and prev_callback is not None:
            try:
                prev_mod, prev_vk = parse_hotkey(prev_hotkey)
                restore = ctypes.windll.user32.RegisterHotKey(  # type: ignore[attr-defined]
                    None, _HOTKEY_ID, prev_mod | _MOD_NOREPEAT, prev_vk
                )
                if restore:
                    _filter = _WindowsNativeEventFilter(
                        hotkey_id=_HOTKEY_ID, callback=prev_callback
                    )
                    app.installNativeEventFilter(_filter)
                    _active_hotkey = prev_hotkey
                    _active_callback = prev_callback
                    logger.info(
                        "Restored previous hotkey %r after failed registration",
                        prev_hotkey,
                    )
                else:
                    logger.warning("Failed to restore previous hotkey %r", prev_hotkey)
            except ValueError:
                logger.warning(
                    "Could not restore previous hotkey %r: parse failed", prev_hotkey
                )
        return False

    _filter = _WindowsNativeEventFilter(hotkey_id=_HOTKEY_ID, callback=callback)
    app.installNativeEventFilter(_filter)
    _active_hotkey = hotkey
    _active_callback = callback
    logger.info("Registered global hotkey %r (id=%s)", hotkey, _HOTKEY_ID)
    return True


def unregister(app: QtWidgets.QApplication) -> None:
    """Unregister the previously registered global hotkey.

    Args:
        app: The running ``QApplication`` instance.
    """
    global _filter, _active_hotkey, _active_callback  # noqa: PLW0603

    if _filter is not None:
        app.removeNativeEventFilter(_filter)
        _filter = None

    _active_hotkey = None
    _active_callback = None

    if sys.platform == "win32":
        ctypes.windll.user32.UnregisterHotKey(  # type: ignore[attr-defined]
            None, _HOTKEY_ID
        )
    logger.debug("Unregistered hotkey (id=%s)", _HOTKEY_ID)


def is_compatible() -> bool:
    """Return ``True`` only on Windows."""
    return sys.platform == "win32"


def is_installed() -> bool:
    """Return ``True``; ctypes is part of the Python standard library."""
    return True
