import pytest
from PySide6 import QtCore, QtGui, QtWidgets

from normcap.gui import settings_dialog


@pytest.fixture
def test_settings(tmp_path):
    settings = QtCore.QSettings(
        str(tmp_path / "test_settings.ini"), QtCore.QSettings.Format.IniFormat
    )
    settings.setValue("notification", True)
    settings.setValue("tray", False)
    settings.setValue("update", True)
    settings.setValue("detect-text", True)
    settings.setValue("detect-codes", True)
    settings.setValue("parse-text", True)
    settings.setValue("language", ["eng"])
    yield settings
    settings.remove("")  # Clear all settings after the test


@pytest.fixture
def all_detection_off_settings(tmp_path):
    settings = QtCore.QSettings(
        str(tmp_path / "test_settings_no_detect.ini"), QtCore.QSettings.Format.IniFormat
    )
    settings.setValue("detect-text", False)
    settings.setValue("detect-codes", False)
    yield settings
    settings.remove("")


@pytest.fixture
def dialog(qtbot, test_settings):
    dlg = settings_dialog.SettingsDialog(
        settings=test_settings,
        installed_languages=["deu", "eng"],
        show_language_manager=True,
    )
    qtbot.addWidget(dlg)
    return dlg


@pytest.fixture
def dialog_no_lang_man(qtbot, test_settings):
    dlg = settings_dialog.SettingsDialog(
        settings=test_settings,
        installed_languages=["eng"],
        show_language_manager=False,
    )
    qtbot.addWidget(dlg)
    return dlg


def test_settings_dialog_creates(dialog):
    # GIVEN a SettingsDialog is instantiated
    # THEN it should be a QDialog
    assert isinstance(dialog, QtWidgets.QDialog)
    assert "NormCap Settings" in dialog.windowTitle()


def test_settings_dialog_has_checkboxes(dialog):
    # GIVEN a SettingsDialog
    # THEN it should contain checkboxes for the main settings
    notification_cb = dialog.findChild(QtWidgets.QCheckBox, "notification")
    tray_cb = dialog.findChild(QtWidgets.QCheckBox, "tray")
    update_cb = dialog.findChild(QtWidgets.QCheckBox, "update")
    detect_text_cb = dialog.findChild(QtWidgets.QCheckBox, "detect-text")
    detect_codes_cb = dialog.findChild(QtWidgets.QCheckBox, "detect-codes")
    parse_text_cb = dialog.findChild(QtWidgets.QCheckBox, "parse-text")

    assert notification_cb is not None
    assert tray_cb is not None
    assert update_cb is not None
    assert detect_text_cb is not None
    assert detect_codes_cb is not None
    assert parse_text_cb is not None


def test_settings_dialog_checkboxes_reflect_settings(dialog):
    # GIVEN a SettingsDialog with known settings values
    notification_cb = dialog.findChild(QtWidgets.QCheckBox, "notification")
    tray_cb = dialog.findChild(QtWidgets.QCheckBox, "tray")
    update_cb = dialog.findChild(QtWidgets.QCheckBox, "update")

    # THEN the checkboxes should reflect the settings values
    assert notification_cb.isChecked() is True
    assert tray_cb.isChecked() is False
    assert update_cb.isChecked() is True


def test_settings_dialog_checkbox_saves_value(dialog):
    # GIVEN a SettingsDialog
    notification_cb = dialog.findChild(QtWidgets.QCheckBox, "notification")

    # WHEN a checkbox is toggled
    original = notification_cb.isChecked()
    notification_cb.setChecked(not original)

    # THEN the settings value should be updated
    assert bool(dialog.settings.value("notification", type=bool)) is not original


def test_settings_dialog_detection_at_least_one(dialog):
    # GIVEN both detection checkboxes are checked
    detect_text_cb = dialog.findChild(QtWidgets.QCheckBox, "detect-text")
    detect_codes_cb = dialog.findChild(QtWidgets.QCheckBox, "detect-codes")
    detect_text_cb.setChecked(True)
    detect_codes_cb.setChecked(True)

    # WHEN both are unchecked (one at a time)
    detect_text_cb.setChecked(False)
    detect_codes_cb.setChecked(False)

    # THEN at least one should remain checked
    assert detect_text_cb.isChecked() or detect_codes_cb.isChecked()


def test_settings_dialog_language_at_least_one(dialog):
    # GIVEN language checkboxes exist
    eng_cb = dialog.findChild(QtWidgets.QCheckBox, "lang_eng")
    deu_cb = dialog.findChild(QtWidgets.QCheckBox, "lang_deu")
    assert eng_cb is not None

    # WHEN all languages are unchecked
    eng_cb.setChecked(True)
    deu_cb.setChecked(False)
    eng_cb.setChecked(False)

    # THEN at least one should remain checked
    assert eng_cb.isChecked() or deu_cb.isChecked()


def test_settings_dialog_has_manage_languages_button(dialog):
    # GIVEN a dialog with language manager enabled
    # THEN it should have the "add/remove …" button
    manage_btn = dialog.findChild(QtWidgets.QPushButton, "manage_languages")
    assert manage_btn is not None
    assert "add/remove" in manage_btn.text()


def test_settings_dialog_manage_languages_emits_signal(qtbot, dialog):
    # GIVEN a SettingsDialog with language manager button
    manage_btn = dialog.findChild(QtWidgets.QPushButton, "manage_languages")

    # WHEN the button is clicked
    # THEN the on_manage_languages signal is emitted
    with qtbot.waitSignal(dialog.com.on_manage_languages, timeout=1000) as result:
        manage_btn.click()
    assert result.signal_triggered


def test_settings_dialog_no_lang_man_has_need_more(dialog_no_lang_man):
    # GIVEN a dialog without language manager
    # THEN it should have the "… need more?" label
    need_more = dialog_no_lang_man.findChild(QtWidgets.QLabel, "show_help_languages")
    assert need_more is not None
    assert "need more" in need_more.text()


def test_settings_dialog_show_introduction_signal(qtbot, dialog):
    # GIVEN a SettingsDialog
    intro_btn = dialog.findChild(QtWidgets.QPushButton, "show_introduction")
    assert intro_btn is not None

    # WHEN the introduction button is clicked
    # THEN the on_show_introduction signal is emitted
    with qtbot.waitSignal(dialog.com.on_show_introduction, timeout=1000) as result:
        intro_btn.click()
    assert result.signal_triggered


def test_settings_dialog_has_version_label(dialog):
    # GIVEN a SettingsDialog
    version_label = dialog.findChild(QtWidgets.QLabel, "version_label")
    # THEN a version label should be present
    assert version_label is not None
    assert "NormCap" in version_label.text()


def test_settings_dialog_detection_normalized_when_all_off(
    qtbot, all_detection_off_settings
):
    # GIVEN a SettingsDialog where all detection settings are disabled
    dlg = settings_dialog.SettingsDialog(
        settings=all_detection_off_settings,
        installed_languages=["eng"],
    )
    qtbot.addWidget(dlg)

    # THEN the first detection checkbox should be auto-checked
    detect_text_cb = dlg.findChild(QtWidgets.QCheckBox, "detect-text")
    detect_codes_cb = dlg.findChild(QtWidgets.QCheckBox, "detect-codes")
    assert detect_text_cb is not None
    assert detect_text_cb.isChecked() or detect_codes_cb.isChecked()
    assert bool(all_detection_off_settings.value("detect-text", type=bool)) is True


def test_settings_dialog_refresh_languages(dialog):
    # GIVEN a SettingsDialog with "deu" and "eng" languages
    assert dialog.findChild(QtWidgets.QCheckBox, "lang_deu") is not None
    assert dialog.findChild(QtWidgets.QCheckBox, "lang_fra") is None

    # WHEN refresh_languages is called with a new list
    dialog.settings.setValue("language", ["eng", "fra"])
    dialog.refresh_languages(["eng", "fra"])

    # THEN the language checkboxes should reflect the new list
    assert dialog.findChild(QtWidgets.QCheckBox, "lang_deu") is None
    assert dialog.findChild(QtWidgets.QCheckBox, "lang_fra") is not None
    assert dialog.findChild(QtWidgets.QCheckBox, "lang_eng") is not None


def test_settings_dialog_on_settings_value_changed_syncs_checkboxes(dialog):
    # GIVEN a SettingsDialog with "eng" active
    eng_cb = dialog.findChild(QtWidgets.QCheckBox, "lang_eng")
    deu_cb = dialog.findChild(QtWidgets.QCheckBox, "lang_deu")
    assert eng_cb.isChecked() is True
    assert deu_cb.isChecked() is False

    # WHEN the language setting changes externally
    dialog._on_settings_value_changed("language", ["deu"])

    # THEN checkboxes should reflect the new setting
    assert eng_cb.isChecked() is False
    assert deu_cb.isChecked() is True


def test_settings_dialog_close_button(qtbot, dialog):
    # GIVEN a SettingsDialog shown to the user
    dialog.show()
    assert dialog.isVisible()

    # WHEN the close button is clicked
    close_btn = dialog.findChild(QtWidgets.QPushButton, "close")
    assert close_btn is not None
    close_btn.click()

    # THEN the dialog should close
    qtbot.waitUntil(lambda: not dialog.isVisible())


def test_settings_dialog_hotkey_widget_created_on_win32(
    qtbot, test_settings, monkeypatch
):
    # GIVEN platform is win32 (any build) and a hotkey is stored in settings
    monkeypatch.setattr(settings_dialog.sys, "platform", "win32")
    test_settings.setValue("hotkey", "ctrl+shift+j")
    dlg = settings_dialog.SettingsDialog(
        settings=test_settings,
        installed_languages=["eng"],
    )
    qtbot.addWidget(dlg)

    # THEN the hotkey widget should be present
    assert dlg._hotkey_edit is not None
    assert dlg.findChild(QtWidgets.QKeySequenceEdit, "hotkey") is not None


def test_settings_dialog_hotkey_widget_present_on_win32_not_packaged(
    qtbot, test_settings, monkeypatch
):
    # GIVEN platform is win32 and not a packaged build
    monkeypatch.setattr(settings_dialog.sys, "platform", "win32")
    monkeypatch.setattr(settings_dialog.info, "is_briefcase_package", lambda: False)
    test_settings.setValue("hotkey", "ctrl+shift+j")
    dlg = settings_dialog.SettingsDialog(
        settings=test_settings,
        installed_languages=["eng"],
    )
    qtbot.addWidget(dlg)

    # THEN the hotkey widget should be present but autostart checkbox absent
    assert dlg._hotkey_edit is not None
    assert dlg._autostart_checkbox is None


def test_settings_dialog_hotkey_widget_absent_on_non_win32(
    qtbot, test_settings, monkeypatch
):
    # GIVEN platform is not win32
    monkeypatch.setattr(settings_dialog.sys, "platform", "linux")
    dlg = settings_dialog.SettingsDialog(
        settings=test_settings,
        installed_languages=["eng"],
    )
    qtbot.addWidget(dlg)

    # THEN no hotkey widget should be created
    assert dlg._hotkey_edit is None


def test_settings_dialog_hotkey_change_saves_to_settings(
    qtbot, test_settings, monkeypatch
):
    # GIVEN a dialog with a hotkey widget on win32
    monkeypatch.setattr(settings_dialog.sys, "platform", "win32")
    test_settings.setValue("hotkey", "ctrl+shift+j")
    dlg = settings_dialog.SettingsDialog(
        settings=test_settings,
        installed_languages=["eng"],
    )
    qtbot.addWidget(dlg)

    # WHEN the hotkey widget sequence is changed
    dlg._hotkey_edit.setKeySequence(QtGui.QKeySequence("Ctrl+A"))

    # THEN the new hotkey should be persisted in settings
    assert str(test_settings.value("hotkey")) == "ctrl+a"


def test_settings_dialog_hotkey_syncs_from_external_change(
    qtbot, test_settings, monkeypatch
):
    # GIVEN a dialog with a hotkey widget on win32
    monkeypatch.setattr(settings_dialog.sys, "platform", "win32")
    test_settings.setValue("hotkey", "ctrl+shift+j")
    dlg = settings_dialog.SettingsDialog(
        settings=test_settings,
        installed_languages=["eng"],
    )
    qtbot.addWidget(dlg)

    # WHEN the hotkey setting changes externally
    dlg._on_settings_value_changed("hotkey", "ctrl+a")

    # THEN the widget should reflect the exact new sequence
    sequence = dlg._hotkey_edit.keySequence()
    assert not sequence.isEmpty()
    stored = sequence.toString(QtGui.QKeySequence.SequenceFormat.PortableText).lower()
    assert stored == "ctrl+a"


def test_settings_dialog_autostart_checkbox_present_on_win32(
    qtbot, test_settings, monkeypatch
):
    # GIVEN platform is win32 and it is a packaged build
    monkeypatch.setattr(settings_dialog.sys, "platform", "win32")
    monkeypatch.setattr(settings_dialog.info, "is_briefcase_package", lambda: True)
    test_settings.setValue("autostart", False)
    dlg = settings_dialog.SettingsDialog(
        settings=test_settings,
        installed_languages=["eng"],
    )
    qtbot.addWidget(dlg)

    # THEN the autostart checkbox should be present
    assert dlg._autostart_checkbox is not None
    assert dlg.findChild(QtWidgets.QCheckBox, "autostart") is not None


def test_settings_dialog_autostart_checkbox_absent_on_non_win32(
    qtbot, test_settings, monkeypatch
):
    # GIVEN platform is not win32
    monkeypatch.setattr(settings_dialog.sys, "platform", "linux")
    dlg = settings_dialog.SettingsDialog(
        settings=test_settings,
        installed_languages=["eng"],
    )
    qtbot.addWidget(dlg)

    # THEN no autostart checkbox should be created
    assert dlg._autostart_checkbox is None


def test_settings_dialog_autostart_checkbox_absent_on_win32_not_packaged(
    qtbot, test_settings, monkeypatch
):
    # GIVEN platform is win32 but not a packaged/Briefcase build
    monkeypatch.setattr(settings_dialog.sys, "platform", "win32")
    monkeypatch.setattr(settings_dialog.info, "is_briefcase_package", lambda: False)
    dlg = settings_dialog.SettingsDialog(
        settings=test_settings,
        installed_languages=["eng"],
    )
    qtbot.addWidget(dlg)

    # THEN no autostart checkbox should be created
    assert dlg._autostart_checkbox is None


def test_settings_dialog_autostart_toggle_persists_to_settings(
    qtbot, test_settings, monkeypatch
):
    # GIVEN a dialog with an autostart checkbox on win32 packaged build
    monkeypatch.setattr(settings_dialog.sys, "platform", "win32")
    monkeypatch.setattr(settings_dialog.info, "is_briefcase_package", lambda: True)
    test_settings.setValue("autostart", False)
    dlg = settings_dialog.SettingsDialog(
        settings=test_settings,
        installed_languages=["eng"],
    )
    qtbot.addWidget(dlg)

    # WHEN the autostart checkbox is toggled
    assert dlg._autostart_checkbox is not None
    dlg._autostart_checkbox.setChecked(True)

    # THEN the settings value should be updated
    assert bool(test_settings.value("autostart", type=bool)) is True


def test_settings_dialog_autostart_syncs_from_external_change(
    qtbot, test_settings, monkeypatch
):
    # GIVEN a dialog with an autostart checkbox on win32 packaged build
    monkeypatch.setattr(settings_dialog.sys, "platform", "win32")
    monkeypatch.setattr(settings_dialog.info, "is_briefcase_package", lambda: True)
    test_settings.setValue("autostart", True)
    dlg = settings_dialog.SettingsDialog(
        settings=test_settings,
        installed_languages=["eng"],
    )
    qtbot.addWidget(dlg)
    assert dlg._autostart_checkbox is not None
    assert dlg._autostart_checkbox.isChecked() is True

    # WHEN the autostart setting changes externally (e.g. reverted on enable failure)
    dlg._on_settings_value_changed("autostart", False)

    # THEN the checkbox should reflect the new state
    assert dlg._autostart_checkbox.isChecked() is False


def test_settings_dialog_has_stylesheet(dialog):
    # GIVEN a SettingsDialog
    # THEN the dialog should have a stylesheet applied
    assert len(dialog.styleSheet()) > 0


def test_settings_dialog_section_title_has_color(dialog):
    # GIVEN a SettingsDialog
    # THEN section title labels should have a non-empty stylesheet (accent color)
    labels = dialog.findChildren(QtWidgets.QLabel)
    titled_labels = [
        label
        for label in labels
        if label.styleSheet()
        and "color" in label.styleSheet()
        and "padding-top" in label.styleSheet()
    ]
    assert len(titled_labels) > 0
