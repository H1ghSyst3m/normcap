import pytest
from PySide6 import QtCore

from normcap.detection import ocr
from normcap.gui import application, introduction
from normcap.gui.settings import Settings


def _make_mock_dialog(autostart_checked: bool, result: introduction.Choice):
    """Return a mock IntroductionDialog class with given checkbox state and result."""

    class _MockDialog:
        def __init__(self, show_on_startup: bool, autostart: bool = False, **kwargs):
            assert isinstance(show_on_startup, bool), (
                "show_on_startup must be forwarded"
            )
            assert isinstance(autostart, bool), "autostart must be forwarded"
            _checked = autostart_checked
            self.autostart_checkbox = type(
                "_CB", (), {"isChecked": lambda s: _checked}
            )()
            self.show_on_startup_checkbox = type(
                "_CB", (), {"isChecked": lambda s: show_on_startup}
            )()

        def exec(self):
            return result

    return _MockDialog


def test_debug_language_manager_is_deactivated(qapp):
    assert not qapp._DEBUG_LANGUAGE_MANAGER


@pytest.mark.parametrize(
    ("active", "available", "sanitized"),
    [
        ("eng", ["eng"], ["eng"]),
        (["eng"], ["deu"], ["deu"]),
        (["eng"], ["afr", "eng"], ["eng"]),
        (["eng"], ["afr", "deu"], ["afr"]),
        (["deu", "eng"], ["afr", "deu"], ["deu"]),
        (["afr", "deu", "eng"], ["afr", "ben", "deu"], ["afr", "deu"]),
    ],
)
def test_sanitize_active_language(qapp, monkeypatch, active, available, sanitized):
    monkeypatch.setattr(ocr.tesseract, "get_languages", lambda **kwargs: available)
    settings = Settings(organization="normcap_TEST")
    try:
        settings.setValue("language", active)
        qapp.settings = settings
        qapp.installed_languages = available
        qapp._sanitize_language_setting()
        assert settings.value("language") == sanitized
    finally:
        for k in settings.allKeys():
            settings.remove(k)


def test_setup_hotkey_registers_on_win32_with_tray(qapp, monkeypatch):
    # GIVEN platform is win32, tray is enabled, and a hotkey is configured
    registered = []
    monkeypatch.setattr(application.sys, "platform", "win32")
    monkeypatch.setattr(
        application.hotkey,
        "register",
        lambda **kwargs: registered.append(kwargs) or True,
    )
    monkeypatch.setattr(application.hotkey, "unregister", lambda **kwargs: None)
    settings = QtCore.QSettings("normcap_hotkey_test_setup", "settings")
    settings.setValue("tray", True)
    settings.setValue("hotkey", "ctrl+shift+j")
    original_settings = qapp.settings
    qapp.settings = settings
    try:
        # WHEN _setup_hotkey is called
        qapp._setup_hotkey()
    finally:
        qapp.settings = original_settings
        settings.remove("")

    # THEN hotkey.register should have been called with the configured hotkey
    assert len(registered) == 1
    assert registered[0]["hotkey"] == "ctrl+shift+j"


def test_setup_hotkey_skips_when_tray_disabled(qapp, monkeypatch):
    # GIVEN platform is win32 but tray is disabled
    registered = []
    monkeypatch.setattr(application.sys, "platform", "win32")
    monkeypatch.setattr(
        application.hotkey,
        "register",
        lambda **kwargs: registered.append(kwargs) or True,
    )
    settings = QtCore.QSettings("normcap_hotkey_test_notray", "settings")
    settings.setValue("tray", False)
    settings.setValue("hotkey", "ctrl+shift+j")
    original_settings = qapp.settings
    qapp.settings = settings
    try:
        # WHEN _setup_hotkey is called
        qapp._setup_hotkey()
    finally:
        qapp.settings = original_settings
        settings.remove("")

    # THEN hotkey.register should not be called
    assert len(registered) == 0


def test_setup_hotkey_skips_on_non_win32(qapp, monkeypatch):
    # GIVEN platform is not win32
    registered = []
    monkeypatch.setattr(application.sys, "platform", "linux")
    monkeypatch.setattr(
        application.hotkey,
        "register",
        lambda **kwargs: registered.append(kwargs) or True,
    )
    settings = QtCore.QSettings("normcap_hotkey_test_nonwin", "settings")
    settings.setValue("tray", True)
    settings.setValue("hotkey", "ctrl+shift+j")
    original_settings = qapp.settings
    qapp.settings = settings
    try:
        # WHEN _setup_hotkey is called
        qapp._setup_hotkey()
    finally:
        qapp.settings = original_settings
        settings.remove("")

    # THEN hotkey.register should not be called
    assert len(registered) == 0


def test_on_hotkey_setting_changed_reregisters(qapp, monkeypatch):
    # GIVEN platform is win32, tray enabled, and a hotkey is configured
    registered = []
    unregistered = []
    monkeypatch.setattr(application.sys, "platform", "win32")
    monkeypatch.setattr(
        application.hotkey,
        "register",
        lambda **kwargs: registered.append(kwargs) or True,
    )
    monkeypatch.setattr(
        application.hotkey,
        "unregister",
        lambda **kwargs: unregistered.append(True),
    )
    settings = QtCore.QSettings("normcap_hotkey_test_changed", "settings")
    settings.setValue("tray", True)
    settings.setValue("hotkey", "ctrl+shift+j")
    original_settings = qapp.settings
    qapp.settings = settings
    try:
        # WHEN a hotkey-related setting changes
        qapp._on_hotkey_setting_changed("hotkey", "ctrl+shift+j")
    finally:
        qapp.settings = original_settings
        settings.remove("")

    # THEN hotkey.register is called directly (atomic swap); unregister is not called
    assert len(unregistered) == 0
    assert len(registered) == 1


def test_on_hotkey_setting_changed_ignores_irrelevant_key(qapp, monkeypatch):
    # GIVEN platform is win32
    unregistered = []
    monkeypatch.setattr(application.sys, "platform", "win32")
    monkeypatch.setattr(
        application.hotkey,
        "unregister",
        lambda **kwargs: unregistered.append(True),
    )

    # WHEN an unrelated setting changes
    qapp._on_hotkey_setting_changed("color", "#FF0000")

    # THEN hotkey.unregister should not be called
    assert len(unregistered) == 0


def test_setup_autostart_enables_on_win32_when_autostart_true(qapp, monkeypatch):
    # GIVEN platform is win32 packaged and autostart is enabled in settings
    enabled = []
    monkeypatch.setattr(application.sys, "platform", "win32")
    monkeypatch.setattr(application.info, "is_briefcase_package", lambda: True)
    monkeypatch.setattr(
        application.autostart, "enable", lambda: enabled.append(True) or True
    )
    monkeypatch.setattr(application.autostart, "disable", lambda: None)
    settings = QtCore.QSettings("normcap_autostart_test_setup", "settings")
    settings.setValue("autostart", True)
    original_settings = qapp.settings
    qapp.settings = settings
    try:
        # WHEN _setup_autostart is called
        qapp._setup_autostart()
    finally:
        qapp.settings = original_settings
        settings.remove("")

    # THEN autostart.enable should have been called
    assert len(enabled) == 1


def test_setup_autostart_disables_on_win32_when_autostart_false(qapp, monkeypatch):
    # GIVEN platform is win32 packaged and autostart is disabled in settings
    disabled = []
    monkeypatch.setattr(application.sys, "platform", "win32")
    monkeypatch.setattr(application.info, "is_briefcase_package", lambda: True)
    monkeypatch.setattr(application.autostart, "enable", lambda: None)
    monkeypatch.setattr(application.autostart, "disable", lambda: disabled.append(True))
    settings = QtCore.QSettings("normcap_autostart_test_setup_off", "settings")
    settings.setValue("autostart", False)
    original_settings = qapp.settings
    qapp.settings = settings
    try:
        # WHEN _setup_autostart is called
        qapp._setup_autostart()
    finally:
        qapp.settings = original_settings
        settings.remove("")

    # THEN autostart.disable should have been called
    assert len(disabled) == 1


def test_setup_autostart_logs_warning_when_enable_fails(qapp, monkeypatch, caplog):
    # GIVEN platform is win32 packaged and autostart.enable() returns False
    import logging

    monkeypatch.setattr(application.sys, "platform", "win32")
    monkeypatch.setattr(application.info, "is_briefcase_package", lambda: True)
    monkeypatch.setattr(application.autostart, "enable", lambda: False)
    monkeypatch.setattr(application.autostart, "disable", lambda: None)
    settings = QtCore.QSettings("normcap_autostart_test_warn", "settings")
    settings.setValue("autostart", True)
    original_settings = qapp.settings
    qapp.settings = settings
    try:
        # WHEN _setup_autostart is called
        with caplog.at_level(logging.WARNING):
            qapp._setup_autostart()
    finally:
        qapp.settings = original_settings
        settings.remove("")

    # THEN a warning should be logged
    assert any("Failed to enable autostart" in r.message for r in caplog.records)


def test_setup_autostart_reverts_setting_when_enable_fails(qapp, monkeypatch):
    # GIVEN platform is win32 packaged and autostart.enable() returns False
    monkeypatch.setattr(application.sys, "platform", "win32")
    monkeypatch.setattr(application.info, "is_briefcase_package", lambda: True)
    monkeypatch.setattr(application.autostart, "enable", lambda: False)
    monkeypatch.setattr(application.autostart, "disable", lambda: None)
    settings = QtCore.QSettings("normcap_autostart_test_revert_startup", "settings")
    settings.setValue("autostart", True)
    original_settings = qapp.settings
    qapp.settings = settings
    try:
        # WHEN _setup_autostart is called and enable fails
        qapp._setup_autostart()
        # THEN the persisted setting should be reverted to False
        assert settings.value("autostart", type=bool) is False
    finally:
        qapp.settings = original_settings
        settings.remove("")


def test_setup_autostart_skips_on_win32_non_packaged(qapp, monkeypatch):
    # GIVEN platform is win32 but not a packaged build
    enabled = []
    monkeypatch.setattr(application.sys, "platform", "win32")
    monkeypatch.setattr(application.info, "is_briefcase_package", lambda: False)
    monkeypatch.setattr(application.autostart, "enable", lambda: enabled.append(True))
    monkeypatch.setattr(application.autostart, "disable", lambda: enabled.append(False))
    settings = QtCore.QSettings("normcap_autostart_test_nonpackaged", "settings")
    settings.setValue("autostart", True)
    original_settings = qapp.settings
    qapp.settings = settings
    try:
        # WHEN _setup_autostart is called
        qapp._setup_autostart()
    finally:
        qapp.settings = original_settings
        settings.remove("")

    # THEN neither enable nor disable should be called
    assert len(enabled) == 0


def test_setup_autostart_skips_on_non_win32(qapp, monkeypatch):
    # GIVEN platform is not win32
    enabled = []
    monkeypatch.setattr(application.sys, "platform", "linux")
    monkeypatch.setattr(application.autostart, "enable", lambda: enabled.append(True))
    monkeypatch.setattr(application.autostart, "disable", lambda: enabled.append(False))
    settings = QtCore.QSettings("normcap_autostart_test_nonwin", "settings")
    settings.setValue("autostart", True)
    original_settings = qapp.settings
    qapp.settings = settings
    try:
        # WHEN _setup_autostart is called
        qapp._setup_autostart()
    finally:
        qapp.settings = original_settings
        settings.remove("")

    # THEN neither enable nor disable should be called
    assert len(enabled) == 0


def test_on_autostart_setting_changed_enables(qapp, monkeypatch):
    # GIVEN platform is win32 packaged and autostart setting changes to True
    enabled = []
    monkeypatch.setattr(application.sys, "platform", "win32")
    monkeypatch.setattr(application.info, "is_briefcase_package", lambda: True)
    monkeypatch.setattr(
        application.autostart, "enable", lambda: enabled.append(True) or True
    )
    monkeypatch.setattr(application.autostart, "disable", lambda: None)
    settings = QtCore.QSettings("normcap_autostart_test_changed_on", "settings")
    settings.setValue("autostart", True)
    original_settings = qapp.settings
    qapp.settings = settings
    try:
        # WHEN the autostart setting changes
        qapp._on_autostart_setting_changed("autostart", True)
    finally:
        qapp.settings = original_settings
        settings.remove("")

    # THEN autostart.enable should have been called
    assert len(enabled) == 1


def test_on_autostart_setting_changed_disables(qapp, monkeypatch):
    # GIVEN platform is win32 packaged and autostart setting changes to False
    disabled = []
    monkeypatch.setattr(application.sys, "platform", "win32")
    monkeypatch.setattr(application.info, "is_briefcase_package", lambda: True)
    monkeypatch.setattr(application.autostart, "enable", lambda: None)
    monkeypatch.setattr(application.autostart, "disable", lambda: disabled.append(True))
    settings = QtCore.QSettings("normcap_autostart_test_changed_off", "settings")
    settings.setValue("autostart", False)
    original_settings = qapp.settings
    qapp.settings = settings
    try:
        # WHEN the autostart setting changes
        qapp._on_autostart_setting_changed("autostart", False)
    finally:
        qapp.settings = original_settings
        settings.remove("")

    # THEN autostart.disable should have been called
    assert len(disabled) == 1


def test_on_autostart_setting_changed_ignores_irrelevant_key(qapp, monkeypatch):
    # GIVEN platform is win32 packaged and an irrelevant setting changes
    called = []
    monkeypatch.setattr(application.sys, "platform", "win32")
    monkeypatch.setattr(application.info, "is_briefcase_package", lambda: True)
    monkeypatch.setattr(application.autostart, "enable", lambda: called.append(True))
    monkeypatch.setattr(application.autostart, "disable", lambda: called.append(False))

    # WHEN an unrelated setting changes
    qapp._on_autostart_setting_changed("color", "#FF0000")

    # THEN neither enable nor disable should be called
    assert len(called) == 0


def test_on_autostart_setting_changed_reverts_setting_when_enable_fails(
    qapp, monkeypatch
):
    # GIVEN platform is win32 packaged and autostart.enable() returns False
    monkeypatch.setattr(application.sys, "platform", "win32")
    monkeypatch.setattr(application.info, "is_briefcase_package", lambda: True)
    monkeypatch.setattr(application.autostart, "enable", lambda: False)
    monkeypatch.setattr(application.autostart, "disable", lambda: None)
    settings = QtCore.QSettings("normcap_autostart_test_revert", "settings")
    settings.setValue("autostart", True)
    original_settings = qapp.settings
    qapp.settings = settings
    try:
        # WHEN the autostart setting is toggled on but enabling fails
        qapp._on_autostart_setting_changed("autostart", True)
    finally:
        qapp.settings = original_settings
        settings.remove("")

    # THEN the setting should have been reverted to False
    assert bool(settings.value("autostart", type=bool)) is False


def test_show_introduction_saves_autostart_when_checkbox_checked(qapp, monkeypatch):
    # GIVEN a mocked dialog that reports the autostart checkbox as checked
    monkeypatch.setattr(
        application.introduction,
        "IntroductionDialog",
        _make_mock_dialog(autostart_checked=True, result=introduction.Choice.SHOW),
    )
    settings = QtCore.QSettings("normcap_intro_autostart_checked", "settings")
    settings.setValue("autostart", False)
    settings.setValue("show-introduction", True)
    original_settings = qapp.settings
    qapp.settings = settings
    try:
        # WHEN show_introduction is called
        qapp.show_introduction()
    finally:
        autostart_saved = settings.value("autostart", type=bool)
        qapp.settings = original_settings
        settings.remove("")

    # THEN the autostart setting should be saved as True
    assert autostart_saved is True


def test_show_introduction_saves_autostart_when_checkbox_unchecked(qapp, monkeypatch):
    # GIVEN a mocked dialog that reports the autostart checkbox as unchecked
    monkeypatch.setattr(
        application.introduction,
        "IntroductionDialog",
        _make_mock_dialog(autostart_checked=False, result=introduction.Choice.SHOW),
    )
    settings = QtCore.QSettings("normcap_intro_autostart_unchecked", "settings")
    settings.setValue("autostart", True)
    settings.setValue("show-introduction", True)
    original_settings = qapp.settings
    qapp.settings = settings
    try:
        # WHEN show_introduction is called
        qapp.show_introduction()
    finally:
        autostart_saved = settings.value("autostart", type=bool)
        qapp.settings = original_settings
        settings.remove("")

    # THEN the autostart setting should be saved as False
    assert autostart_saved is False


def test_show_introduction_does_not_save_autostart_when_rejected(qapp, monkeypatch):
    # GIVEN a mocked dialog that is rejected (closed via X)
    monkeypatch.setattr(
        application.introduction,
        "IntroductionDialog",
        _make_mock_dialog(autostart_checked=True, result=introduction.Choice.REJECTED),
    )
    settings = QtCore.QSettings("normcap_intro_autostart_rejected", "settings")
    settings.setValue("autostart", False)
    settings.setValue("show-introduction", True)
    original_settings = qapp.settings
    qapp.settings = settings
    try:
        # WHEN show_introduction is called but the dialog is rejected
        qapp.show_introduction()
    finally:
        autostart_saved = settings.value("autostart", type=bool)
        qapp.settings = original_settings
        settings.remove("")

    # THEN the autostart setting should remain unchanged
    assert autostart_saved is False
