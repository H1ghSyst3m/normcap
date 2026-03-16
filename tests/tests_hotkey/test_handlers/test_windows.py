import ctypes
import sys
from typing import cast
from unittest.mock import MagicMock, patch

import pytest
from PySide6 import QtWidgets

from normcap.hotkey.handlers import windows


@pytest.fixture(autouse=True)
def _reset_windows_state():
    windows._filter = None
    windows._active_hotkey = None
    windows._active_callback = None
    yield
    windows._filter = None
    windows._active_hotkey = None
    windows._active_callback = None


@pytest.mark.parametrize(
    ("platform", "result"),
    [("win32", True), ("darwin", False), ("linux", False)],
)
def test_windows_is_compatible(monkeypatch, platform, result):
    monkeypatch.setattr(windows.sys, "platform", platform)
    assert windows.is_compatible() == result


def test_windows_is_installed():
    assert windows.is_installed() is True


@pytest.mark.parametrize(
    ("hotkey", "expected_mods", "expected_vk"),
    [
        (
            "ctrl+shift+j",
            windows._MOD_CONTROL | windows._MOD_SHIFT,
            ord("J"),
        ),
        (
            "ctrl+a",
            windows._MOD_CONTROL,
            ord("A"),
        ),
        (
            "alt+f4",
            windows._MOD_ALT,
            windows._VK_MAP["f4"],
        ),
        (
            "ctrl+shift+f12",
            windows._MOD_CONTROL | windows._MOD_SHIFT,
            windows._VK_MAP["f12"],
        ),
        (
            "ctrl+alt+delete",
            windows._MOD_CONTROL | windows._MOD_ALT,
            windows._VK_MAP["delete"],
        ),
        (
            "win+r",
            windows._MOD_WIN,
            ord("R"),
        ),
    ],
)
def test_parse_hotkey(hotkey, expected_mods, expected_vk):
    mods, vk = windows.parse_hotkey(hotkey)
    assert mods == expected_mods
    assert vk == expected_vk


def test_parse_hotkey_empty_raises():
    with pytest.raises(ValueError, match="Invalid hotkey"):
        windows.parse_hotkey("")


def test_parse_hotkey_unknown_key_raises():
    with pytest.raises(ValueError, match="Unknown key"):
        windows.parse_hotkey("ctrl+unknownkey")


def test_parse_hotkey_multiple_non_modifier_keys_raises():
    with pytest.raises(ValueError, match="Multiple non-modifier"):
        windows.parse_hotkey("ctrl+a+b")


def test_parse_hotkey_only_modifiers_raises():
    with pytest.raises(ValueError, match="No non-modifier"):
        windows.parse_hotkey("ctrl+shift")


def test_register_and_unregister(qapp, monkeypatch):
    mock_register = MagicMock(return_value=1)
    mock_unregister = MagicMock(return_value=1)

    monkeypatch.setattr(windows, "_filter", None)

    class FakeUser32:
        RegisterHotKey = staticmethod(mock_register)
        UnregisterHotKey = staticmethod(mock_unregister)

    class FakeWindll:
        user32 = FakeUser32()

    monkeypatch.setattr(ctypes, "windll", FakeWindll(), raising=False)
    monkeypatch.setattr(windows.sys, "platform", "win32")

    triggered = []
    result = windows.register(
        hotkey="ctrl+shift+j",
        app=qapp,
        callback=lambda: triggered.append(True),
    )
    assert result is True
    mock_register.assert_called_once()
    assert mock_register.call_args[0][1] == windows._HOTKEY_ID
    # windows.register calls unregister internally before the OS registration
    assert mock_unregister.call_count == 1

    windows.unregister(app=qapp)
    assert mock_unregister.call_count == 2
    assert mock_unregister.call_args[0][1] == windows._HOTKEY_ID


def test_register_empty_hotkey_returns_false(qapp):
    result = windows.register(hotkey="", app=qapp, callback=lambda: None)
    assert result is False


def test_register_invalid_hotkey_returns_false(qapp, monkeypatch):
    monkeypatch.setattr(windows.sys, "platform", "win32")
    monkeypatch.setattr(windows, "_filter", None)
    result = windows.register(
        hotkey="ctrl+badtoken",
        app=qapp,
        callback=lambda: None,
    )
    assert result is False


@pytest.mark.skipif(sys.platform == "win32", reason="Non-Windows specific test")
def test_register_on_non_win32_raises():
    # On non-Windows, ctypes.windll is not available.
    # The AttributeError is raised before app is accessed (no filter is registered).
    app = cast(QtWidgets.QApplication, None)
    with pytest.raises(AttributeError):
        windows.register(hotkey="ctrl+shift+j", app=app, callback=lambda: None)


@pytest.mark.parametrize(
    ("hotkey", "expected_vk"),
    [
        ("ctrl+plus", 0xBB),
        ("ctrl+minus", 0xBD),
        ("ctrl+equal", 0xBB),
        ("ctrl+semicolon", 0xBA),
        ("ctrl+comma", 0xBC),
        ("ctrl+period", 0xBE),
        ("ctrl+slash", 0xBF),
        ("ctrl+bracketleft", 0xDB),
        ("ctrl+bracketright", 0xDD),
        ("ctrl+backslash", 0xDC),
        ("ctrl+apostrophe", 0xDE),
        ("ctrl+quoteleft", 0xC0),
    ],
)
def test_parse_hotkey_portabletext_punctuation(hotkey, expected_vk):
    mods, vk = windows.parse_hotkey(hotkey)
    assert mods == windows._MOD_CONTROL
    assert vk == expected_vk


def test_native_event_filter_handles_dispatcher_msg():
    triggered = []
    event_filter = windows._WindowsNativeEventFilter(
        hotkey_id=windows._HOTKEY_ID, callback=lambda: triggered.append(True)
    )

    fake_msg = MagicMock()
    fake_msg.message = windows._WM_HOTKEY
    fake_msg.wParam = windows._HOTKEY_ID

    with patch("ctypes.wintypes.MSG.from_address", return_value=fake_msg):
        handled, code = event_filter.nativeEventFilter(b"windows_dispatcher_MSG", 12345)
    assert handled is True
    assert code == 0
    assert triggered == [True]


def test_native_event_filter_ignores_unconvertible_message():
    event_filter = windows._WindowsNativeEventFilter(
        hotkey_id=windows._HOTKEY_ID, callback=lambda: None
    )
    handled, code = event_filter.nativeEventFilter(b"windows_generic_MSG", object())
    assert handled is False
    assert code == 0
