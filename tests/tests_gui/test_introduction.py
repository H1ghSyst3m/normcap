from pathlib import Path

import pytest
from PySide6 import QtCore, QtWidgets

from normcap.gui import introduction


@pytest.mark.parametrize("show_on_startup", [True, False])
def test_introduction_initialize_checkbox_state(show_on_startup):
    # GIVEN the introduction dialog
    # WHEN the dialog is instantiated with a certain argument
    dialog = introduction.IntroductionDialog(show_on_startup=show_on_startup)

    # THEN the checkbox should be set accordingly
    assert dialog.show_on_startup_checkbox.isChecked() is show_on_startup


@pytest.mark.gui
@pytest.mark.parametrize(
    ("show_on_startup", "expected_return_code"),
    [(True, introduction.Choice.SHOW), (False, introduction.Choice.DONT_SHOW)],
)
def test_introduction_checkbox_sets_return_code(
    qtbot, show_on_startup, expected_return_code
):
    # GIVEN the dialog is initialized with a certain argument value
    dialog = introduction.IntroductionDialog(show_on_startup=show_on_startup)
    qtbot.addWidget(dialog)

    # WHEN the dialog is shown and the close button is clicked
    def close_dialog():
        while not dialog.isVisible():
            ...
        dialog.ok_button.click()

    QtCore.QTimer.singleShot(0, close_dialog)
    return_code = dialog.exec()

    # THEN the return code should be set accordingly
    assert return_code == expected_return_code


@pytest.mark.gui
@pytest.mark.parametrize(
    ("show_on_startup", "expected_return_code"),
    [(False, introduction.Choice.SHOW), (True, introduction.Choice.DONT_SHOW)],
)
def test_introduction_toggle_checkbox_changes_return_code(
    qtbot, show_on_startup, expected_return_code
):
    # GIVEN the dialog is initialized with a certain argument value
    dialog = introduction.IntroductionDialog(show_on_startup=show_on_startup)
    qtbot.addWidget(dialog)

    # WHEN the dialog is shown and the close button is clicked
    def close_dialog():
        while not dialog.isVisible():
            ...
        dialog.show_on_startup_checkbox.click()
        dialog.ok_button.click()

    QtCore.QTimer.singleShot(0, close_dialog)
    return_code = dialog.exec()

    # THEN the return code should be set accordingly
    assert return_code == expected_return_code


def test_introduction_autostart_checkbox_absent_on_non_win32(monkeypatch):
    # GIVEN a non-Windows platform
    monkeypatch.setattr(introduction.sys, "platform", "linux")

    # WHEN the dialog is instantiated
    dialog = introduction.IntroductionDialog(show_on_startup=True)

    # THEN the autostart checkbox should not be present
    assert dialog.autostart_checkbox is None


def test_introduction_autostart_checkbox_absent_on_win32_non_packaged(monkeypatch):
    # GIVEN Windows platform but not a briefcase package
    monkeypatch.setattr(introduction.sys, "platform", "win32")
    monkeypatch.setattr(introduction.info, "is_briefcase_package", lambda: False)

    # WHEN the dialog is instantiated
    dialog = introduction.IntroductionDialog(show_on_startup=True)

    # THEN the autostart checkbox should not be present
    assert dialog.autostart_checkbox is None


def test_introduction_autostart_checkbox_present_on_win32_packaged(monkeypatch):
    # GIVEN Windows platform and a briefcase package
    monkeypatch.setattr(introduction.sys, "platform", "win32")
    monkeypatch.setattr(introduction.info, "is_briefcase_package", lambda: True)

    # WHEN the dialog is instantiated with autostart=True
    dialog = introduction.IntroductionDialog(show_on_startup=True, autostart=True)

    # THEN the autostart checkbox should be present and checked
    assert dialog.autostart_checkbox is not None
    assert dialog.autostart_checkbox.isChecked() is True


def test_introduction_autostart_checkbox_unchecked_when_false(monkeypatch):
    # GIVEN Windows platform and a briefcase package
    monkeypatch.setattr(introduction.sys, "platform", "win32")
    monkeypatch.setattr(introduction.info, "is_briefcase_package", lambda: True)

    # WHEN the dialog is instantiated with autostart=False
    dialog = introduction.IntroductionDialog(show_on_startup=True, autostart=False)

    # THEN the autostart checkbox should be present but unchecked
    assert dialog.autostart_checkbox is not None
    assert dialog.autostart_checkbox.isChecked() is False


def test_introduction_hotkey_section_present_on_win32(monkeypatch):
    # GIVEN Windows platform and translation disabled (identity function)
    monkeypatch.setattr(introduction.sys, "platform", "win32")
    monkeypatch.setattr(introduction, "_", lambda x: x)

    # WHEN the dialog sections are retrieved
    dialog = introduction.IntroductionDialog(show_on_startup=True)
    titles = [s.title.lower() for s in dialog.sections_data]

    # THEN a hotkey/global section should be present
    assert any("hotkey" in t or "global" in t for t in titles)


def test_introduction_hotkey_section_absent_on_non_win32(monkeypatch):
    # GIVEN a non-Windows platform and translation disabled (identity function)
    monkeypatch.setattr(introduction.sys, "platform", "linux")
    monkeypatch.setattr(introduction, "_", lambda x: x)

    # WHEN the dialog sections are retrieved
    dialog = introduction.IntroductionDialog(show_on_startup=True)
    titles = [s.title.lower() for s in dialog.sections_data]

    # THEN no hotkey/global section should be present
    assert not any("hotkey" in t or "global" in t for t in titles)


def test_introduction_hotkey_section_mentions_default_shortcut(monkeypatch):
    # GIVEN Windows platform and translation disabled (identity function)
    monkeypatch.setattr(introduction.sys, "platform", "win32")
    monkeypatch.setattr(introduction, "_", lambda x: x)

    # WHEN the dialog sections are retrieved
    dialog = introduction.IntroductionDialog(show_on_startup=True)
    hotkey_sections = [
        s
        for s in dialog.sections_data
        if "hotkey" in s.title.lower() or "global" in s.title.lower()
    ]

    # THEN the hotkey section text should mention the default shortcut
    assert hotkey_sections
    assert "ctrl+shift+j" in hotkey_sections[0].text.lower()


def test_introduction_settings_section_mentions_both_menus(monkeypatch):
    # GIVEN the introduction dialog with translation disabled (identity function)
    monkeypatch.setattr(introduction, "_", lambda x: x)
    dialog = introduction.IntroductionDialog(show_on_startup=True)
    settings_sections = [
        s for s in dialog.sections_data if "settings" in s.title.lower()
    ]

    # THEN the settings section text should mention both gear icon and settings dialog
    assert settings_sections
    text = settings_sections[0].text.lower()
    assert "gear" in text
    assert "settings" in text


def test_introduction_missing_image_shows_section_title_as_placeholder():
    # GIVEN a section with a title and a path that does not exist
    section_title = "My Missing Image Section"
    missing_image = Path("/nonexistent/path/missing-image.png")

    # WHEN _create_content_section is called with the missing image
    layout = introduction.IntroductionDialog._create_content_section(
        title=section_title, text="Some description text.", image=missing_image
    )

    # THEN the image label (fixed 230x400) should display the section title
    image_label = None
    for i in range(layout.count()):
        item = layout.itemAt(i)
        widget = item.widget() if item else None
        if (
            isinstance(widget, QtWidgets.QLabel)
            and widget.minimumWidth() == 230
            and widget.maximumWidth() == 230
            and widget.minimumHeight() == 400
            and widget.maximumHeight() == 400
        ):
            image_label = widget
            break

    assert image_label is not None, "Expected a fixed-size image QLabel in the layout"
    assert image_label.text() == section_title
