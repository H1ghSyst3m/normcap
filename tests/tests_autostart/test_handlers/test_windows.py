import sys
from unittest.mock import MagicMock, patch

import pytest

from normcap.autostart.handlers import windows


@pytest.mark.parametrize(
    ("platform", "packaged", "result"),
    [
        ("win32", True, True),
        ("win32", False, False),
        ("darwin", True, False),
        ("linux", True, False),
    ],
)
def test_windows_is_compatible(monkeypatch, platform, packaged, result):
    monkeypatch.setattr(windows.sys, "platform", platform)
    monkeypatch.setattr(windows.info, "is_briefcase_package", lambda: packaged)
    assert windows.is_compatible() == result


def test_windows_is_installed():
    assert windows.is_installed() is True


def test_enable_writes_registry_key():
    # GIVEN a mocked winreg module
    mock_winreg = MagicMock()
    mock_key = MagicMock()
    mock_winreg.OpenKey.return_value.__enter__ = MagicMock(return_value=mock_key)
    mock_winreg.OpenKey.return_value.__exit__ = MagicMock(return_value=False)
    mock_winreg.HKEY_CURRENT_USER = "HKCU"
    mock_winreg.KEY_SET_VALUE = 0x0002
    mock_winreg.REG_SZ = 1

    with patch.dict("sys.modules", {"winreg": mock_winreg}):
        # WHEN enable() is called
        result = windows.enable()

    # THEN the registry key is written with the correct path and value
    assert result is True
    mock_winreg.OpenKey.assert_called_once_with(
        mock_winreg.HKEY_CURRENT_USER,
        windows._REG_PATH,
        0,
        mock_winreg.KEY_SET_VALUE,
    )
    mock_winreg.SetValueEx.assert_called_once()
    call_args = mock_winreg.SetValueEx.call_args[0]
    assert call_args[1] == windows._REG_KEY
    assert "--background-mode" in call_args[4]


def test_enable_returns_false_on_error():
    # GIVEN a mocked winreg where OpenKey raises OSError
    mock_winreg = MagicMock()
    mock_winreg.OpenKey.side_effect = OSError("access denied")
    mock_winreg.HKEY_CURRENT_USER = "HKCU"
    mock_winreg.KEY_SET_VALUE = 0x0002

    with patch.dict("sys.modules", {"winreg": mock_winreg}):
        # WHEN enable() is called
        result = windows.enable()

    # THEN it should return False without raising
    assert result is False


def test_disable_deletes_registry_key():
    # GIVEN a mocked winreg module
    mock_winreg = MagicMock()
    mock_key = MagicMock()
    mock_winreg.OpenKey.return_value.__enter__ = MagicMock(return_value=mock_key)
    mock_winreg.OpenKey.return_value.__exit__ = MagicMock(return_value=False)
    mock_winreg.HKEY_CURRENT_USER = "HKCU"
    mock_winreg.KEY_SET_VALUE = 0x0002

    with patch.dict("sys.modules", {"winreg": mock_winreg}):
        # WHEN disable() is called
        windows.disable()

    # THEN the registry value is deleted
    mock_winreg.DeleteValue.assert_called_once_with(mock_key, windows._REG_KEY)


def test_disable_is_silent_when_key_absent():
    # GIVEN a mocked winreg where DeleteValue raises FileNotFoundError
    mock_winreg = MagicMock()
    mock_key = MagicMock()
    mock_winreg.OpenKey.return_value.__enter__ = MagicMock(return_value=mock_key)
    mock_winreg.OpenKey.return_value.__exit__ = MagicMock(return_value=False)
    mock_winreg.HKEY_CURRENT_USER = "HKCU"
    mock_winreg.KEY_SET_VALUE = 0x0002
    mock_winreg.DeleteValue.side_effect = FileNotFoundError

    with patch.dict("sys.modules", {"winreg": mock_winreg}):
        # WHEN disable() is called and registry value does not exist
        # THEN no exception should be raised
        windows.disable()


def test_disable_is_silent_on_oserror():
    # GIVEN a mocked winreg where OpenKey raises OSError
    mock_winreg = MagicMock()
    mock_winreg.OpenKey.side_effect = OSError("access denied")
    mock_winreg.HKEY_CURRENT_USER = "HKCU"
    mock_winreg.KEY_SET_VALUE = 0x0002

    with patch.dict("sys.modules", {"winreg": mock_winreg}):
        # WHEN disable() is called and registry access is denied
        # THEN no exception should be raised
        windows.disable()


def test_is_enabled_returns_true_when_key_exists():
    # GIVEN a mocked winreg where QueryValueEx succeeds
    mock_winreg = MagicMock()
    mock_key = MagicMock()
    mock_winreg.OpenKey.return_value.__enter__ = MagicMock(return_value=mock_key)
    mock_winreg.OpenKey.return_value.__exit__ = MagicMock(return_value=False)
    mock_winreg.HKEY_CURRENT_USER = "HKCU"
    mock_winreg.KEY_READ = 0x20019
    mock_winreg.QueryValueEx.return_value = ("some_value", 1)

    with patch.dict("sys.modules", {"winreg": mock_winreg}):
        result = windows.is_enabled()

    assert result is True


def test_is_enabled_returns_false_when_key_absent():
    # GIVEN a mocked winreg that raises FileNotFoundError on OpenKey
    mock_winreg = MagicMock()
    mock_winreg.OpenKey.side_effect = FileNotFoundError

    with patch.dict("sys.modules", {"winreg": mock_winreg}):
        result = windows.is_enabled()

    assert result is False


def test_is_enabled_returns_false_on_oserror():
    # GIVEN a mocked winreg that raises OSError on OpenKey
    mock_winreg = MagicMock()
    mock_winreg.OpenKey.side_effect = OSError("access denied")
    mock_winreg.HKEY_CURRENT_USER = "HKCU"
    mock_winreg.KEY_READ = 0x20019

    with patch.dict("sys.modules", {"winreg": mock_winreg}):
        result = windows.is_enabled()

    assert result is False


@pytest.mark.skipif(sys.platform == "win32", reason="Non-Windows specific test")
def test_enable_on_non_win32_raises():
    # On non-Windows, winreg is not available.
    with pytest.raises((ImportError, ModuleNotFoundError)):
        windows.enable()


@pytest.mark.skipif(sys.platform == "win32", reason="Non-Windows specific test")
def test_disable_on_non_win32_raises():
    # On non-Windows, winreg is not available.
    with pytest.raises((ImportError, ModuleNotFoundError)):
        windows.disable()


@pytest.mark.skipif(sys.platform == "win32", reason="Non-Windows specific test")
def test_is_enabled_on_non_win32_raises():
    # On non-Windows, winreg is not available.
    with pytest.raises((ImportError, ModuleNotFoundError)):
        windows.is_enabled()
