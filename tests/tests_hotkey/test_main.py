from typing import cast

import pytest
from PySide6 import QtWidgets

from normcap.hotkey import main
from normcap.hotkey.handlers import windows


def _null_app() -> QtWidgets.QApplication:
    """Return a null app reference for tests where the app won't be accessed."""
    return cast(QtWidgets.QApplication, None)


@pytest.fixture(autouse=True)
def _reset_active_handler():
    main._active_handler = None
    yield
    main._active_handler = None


def test_get_available_handlers_no_compatible(monkeypatch):
    # GIVEN a system is mocked to not support any hotkey handler
    for handler in main._hotkey_handlers.values():
        monkeypatch.setattr(handler, "is_compatible", lambda: False)

    # WHEN we ask for available handlers
    result = main.get_available_handlers()

    # THEN we expect an empty list
    assert result == []


def test_get_available_handlers_compatible_but_not_installed(monkeypatch):
    # GIVEN a system where handlers are compatible but not installed
    for handler in main._hotkey_handlers.values():
        monkeypatch.setattr(handler, "is_compatible", lambda: True)
        monkeypatch.setattr(handler, "is_installed", lambda: False)

    # WHEN we ask for available handlers
    result = main.get_available_handlers()

    # THEN we expect an empty list
    assert result == []


def test_register_without_compatible_handler_fails(monkeypatch):
    # GIVEN a system with no compatible hotkey handler
    for handler in main._hotkey_handlers.values():
        monkeypatch.setattr(handler, "is_compatible", lambda: False)

    # WHEN we try to register a hotkey
    result = main.register(
        hotkey="ctrl+shift+j", app=_null_app(), callback=lambda: None
    )

    # THEN we expect a failure
    assert result is False


def test_unregister_without_compatible_handler_is_safe(monkeypatch):
    # GIVEN a system with no compatible hotkey handler
    for handler in main._hotkey_handlers.values():
        monkeypatch.setattr(handler, "is_compatible", lambda: False)

    # WHEN we call unregister
    # THEN no exception should be raised
    main.unregister(app=_null_app())


def test_register_calls_handler(monkeypatch):
    # GIVEN a mock handler that is compatible and installed
    called_with = {}

    def mock_register(
        hotkey: str, app: object, callback: object
    ) -> bool:
        called_with["hotkey"] = hotkey
        return True

    monkeypatch.setattr(windows, "is_compatible", lambda: True)
    monkeypatch.setattr(windows, "is_installed", lambda: True)
    monkeypatch.setattr(windows, "register", mock_register)

    # WHEN we register a hotkey
    result = main.register(
        hotkey="ctrl+shift+j", app=_null_app(), callback=lambda: None
    )

    # THEN the handler was called with the right hotkey
    assert result is True
    assert called_with.get("hotkey") == "ctrl+shift+j"
