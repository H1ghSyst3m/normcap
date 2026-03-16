"""Windows autostart handler using the Windows registry."""

import logging
import sys

from normcap.system import info

logger = logging.getLogger(__name__)

install_instructions = ""
_REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
_REG_KEY = "NormCap"


def enable() -> bool:
    r"""Register NormCap in ``HKCU\Software\Microsoft\Windows\CurrentVersion\Run``.

    Returns:
        ``True`` if registration succeeded, ``False`` otherwise.
    """
    import winreg

    command = f'"{sys.executable}" --background-mode'
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            _REG_PATH,
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            winreg.SetValueEx(key, _REG_KEY, 0, winreg.REG_SZ, command)
    except OSError:
        logger.exception("Failed to write autostart registry key")
        return False
    logger.info("Autostart enabled: %r", command)
    return True


def disable() -> None:
    """Remove the NormCap autostart registry entry."""
    import winreg

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            _REG_PATH,
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            winreg.DeleteValue(key, _REG_KEY)
        logger.info("Autostart disabled.")
    except FileNotFoundError:
        logger.debug("Autostart registry key not found; nothing to delete.")
    except OSError:
        logger.exception("Failed to delete autostart registry key")


def is_enabled() -> bool:
    """Return ``True`` if the NormCap autostart registry entry exists."""
    import winreg

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            _REG_PATH,
            0,
            winreg.KEY_READ,
        ) as key:
            winreg.QueryValueEx(key, _REG_KEY)
    except FileNotFoundError:
        return False
    except OSError:
        logger.exception("Failed to read autostart registry key")
        return False
    else:
        return True


def is_compatible() -> bool:
    """Return ``True`` on Briefcase-packaged Windows builds."""
    return sys.platform == "win32" and info.is_briefcase_package()


def is_installed() -> bool:
    """Return ``True``; winreg is stdlib."""
    return True
