from normcap.autostart import main
from normcap.autostart.handlers import windows


def test_get_available_handlers_no_compatible(monkeypatch):
    # GIVEN a system is mocked to not support any autostart handler
    for handler in main._autostart_handlers.values():
        monkeypatch.setattr(handler, "is_compatible", lambda: False)

    # WHEN we ask for available handlers
    result = main.get_available_handlers()

    # THEN we expect an empty list
    assert result == []


def test_get_available_handlers_compatible_but_not_installed(monkeypatch):
    # GIVEN a system where handlers are compatible but not installed
    for handler in main._autostart_handlers.values():
        monkeypatch.setattr(handler, "is_compatible", lambda: True)
        monkeypatch.setattr(handler, "is_installed", lambda: False)

    # WHEN we ask for available handlers
    result = main.get_available_handlers()

    # THEN we expect an empty list
    assert result == []


def test_enable_without_compatible_handler_is_safe(monkeypatch):
    # GIVEN a system with no compatible autostart handler
    for handler in main._autostart_handlers.values():
        monkeypatch.setattr(handler, "is_compatible", lambda: False)

    # WHEN we call enable
    result = main.enable()

    # THEN no exception should be raised and False is returned
    assert result is False


def test_disable_without_compatible_handler_is_safe(monkeypatch):
    # GIVEN a system with no compatible autostart handler
    for handler in main._autostart_handlers.values():
        monkeypatch.setattr(handler, "is_compatible", lambda: False)

    # WHEN we call disable
    # THEN no exception should be raised
    main.disable()


def test_is_enabled_without_compatible_handler_returns_false(monkeypatch):
    # GIVEN a system with no compatible autostart handler
    for handler in main._autostart_handlers.values():
        monkeypatch.setattr(handler, "is_compatible", lambda: False)

    # WHEN we call is_enabled
    result = main.is_enabled()

    # THEN we expect False
    assert result is False


def test_enable_returns_false_and_logs_warning_when_all_handlers_fail(
    monkeypatch, caplog
):
    import logging

    # GIVEN a handler that is compatible and installed but enable() returns False
    monkeypatch.setattr(windows, "is_compatible", lambda: True)
    monkeypatch.setattr(windows, "is_installed", lambda: True)
    monkeypatch.setattr(windows, "enable", lambda: False)

    # WHEN we call enable
    with caplog.at_level(logging.WARNING):
        result = main.enable()

    # THEN False is returned and a warning is logged
    assert result is False
    assert any(
        "all available autostart handlers failed" in r.message for r in caplog.records
    )


def test_enable_calls_handler(monkeypatch):
    # GIVEN a mock handler that is compatible and installed
    called = []

    monkeypatch.setattr(windows, "is_compatible", lambda: True)
    monkeypatch.setattr(windows, "is_installed", lambda: True)
    monkeypatch.setattr(windows, "enable", lambda: called.append(True) or True)

    # WHEN we call enable
    result = main.enable()

    # THEN the handler was called and True is returned
    assert called == [True]
    assert result is True


def test_disable_calls_handler(monkeypatch):
    # GIVEN a mock handler that is compatible and installed
    called = []

    monkeypatch.setattr(windows, "is_compatible", lambda: True)
    monkeypatch.setattr(windows, "is_installed", lambda: True)
    monkeypatch.setattr(windows, "disable", lambda: called.append(True))

    # WHEN we call disable
    main.disable()

    # THEN the handler was called
    assert called == [True]


def test_disable_logs_debug_when_no_handler(monkeypatch, caplog):
    import logging

    # GIVEN no compatible handler
    for handler in main._autostart_handlers.values():
        monkeypatch.setattr(handler, "is_compatible", lambda: False)

    # WHEN we call disable
    with caplog.at_level(logging.DEBUG):
        main.disable()

    # THEN a debug message is logged
    assert any("skipping disable" in r.message for r in caplog.records)


def test_is_enabled_delegates_to_handler(monkeypatch):
    # GIVEN a mock handler that reports autostart is enabled
    monkeypatch.setattr(windows, "is_compatible", lambda: True)
    monkeypatch.setattr(windows, "is_installed", lambda: True)
    monkeypatch.setattr(windows, "is_enabled", lambda: True)

    # WHEN we call is_enabled
    result = main.is_enabled()

    # THEN the result matches what the handler reported
    assert result is True


def test_is_enabled_returns_false_when_handler_reports_disabled(monkeypatch):
    # GIVEN a mock handler that reports autostart is not enabled
    monkeypatch.setattr(windows, "is_compatible", lambda: True)
    monkeypatch.setattr(windows, "is_installed", lambda: True)
    monkeypatch.setattr(windows, "is_enabled", lambda: False)

    # WHEN we call is_enabled
    result = main.is_enabled()

    # THEN False is returned
    assert result is False
