import pytest
from PySide6 import QtGui, QtWidgets

from normcap.detection import ocr
from normcap.gui.application import screenshot

from .testcases import testcases


@pytest.mark.gui
def test_settings_menu_creates_actions(monkeypatch, qtbot, qapp):
    """Test if capture mode can be started through tray icon."""
    # GIVEN NormCap is started with any image as screenshot
    some_image = testcases[0].screenshot
    monkeypatch.setattr(screenshot, "capture", lambda: [some_image])
    qapp._show_windows(delay_screenshot=False)

    # WHEN the menu button is clicked (mocked here via aboutToShow, because menus are
    #    hard to test as they have their own event loops
    menu = qapp.windows[0].findChild(QtWidgets.QToolButton, "settings_icon").menu()
    menu.aboutToShow.emit()
    qtbot.wait(200)

    # THEN various actions should be available in the menu
    actions = menu.actions()
    assert len(actions) > 10

    texts = [a.text().lower() for a in actions]
    assert "show notification" in texts
    assert "parse text" in texts
    assert "languages" in texts
    assert "about" in texts
    assert "close" in texts


@pytest.mark.gui
def test_settings_menu_close_action_exits(monkeypatch, qtbot, qapp, test_signal):
    """Tests complete OCR workflow."""

    # GIVEN NormCap is started with any image as screenshot
    #   and tray icon is disabled
    some_image = testcases[0].screenshot
    monkeypatch.setattr(screenshot, "capture", lambda: [some_image])

    original_value_func = qapp.settings.value

    def _mocked_settings(*args, **kwargs):
        if "tray" in args:
            return False
        return original_value_func(*args, **kwargs)

    monkeypatch.setattr(qapp.settings, "value", _mocked_settings)
    qapp._show_windows(delay_screenshot=False)

    # WHEN the menu button is clicked (mocked here via aboutToShow, because menus are
    #    hard to test as they have their own event loops)
    #    and the "close" action is triggered
    menu = qapp.windows[0].findChild(QtWidgets.QToolButton, "settings_icon").menu()
    menu.aboutToShow.emit()
    qtbot.wait(200)

    actions = menu.actions()
    close_action = next(a for a in actions if a.text().lower() == "close")
    with qtbot.waitSignal(qapp.com.on_exit_application):
        close_action.trigger()


@pytest.mark.gui
def test_settings_menu_close_action_minimizes(monkeypatch, qtbot, qapp):
    """Tests complete OCR workflow."""
    # GIVEN NormCap is started with any image as screenshot
    #   and tray icon is enabled
    some_image = testcases[0].screenshot
    monkeypatch.setattr(screenshot, "capture", lambda: [some_image])
    qapp._show_windows(delay_screenshot=False)

    # WHEN the menu button is clicked (mocked here via aboutToShow, because menus are
    #    hard to test as they have their own event loops)
    #    and the "close" action is triggered
    menu = qapp.windows[0].findChild(QtWidgets.QToolButton, "settings_icon").menu()
    menu.aboutToShow.emit()
    qtbot.wait(200)

    with qtbot.waitSignal(qapp.com.on_windows_closed):
        actions = menu.actions()
        close_action = next(a for a in actions if a.text().lower() == "close")
        close_action.trigger()

    # THEN normcap should not exit
    #   and all windows should be deleted
    qtbot.assertNotEmitted(qapp.com.on_exit_application, wait=200)
    assert qapp.windows == {}


@pytest.mark.gui
def test_update_installed_languages_updates_menu_buttons(monkeypatch, qtbot, qapp):
    """Test _update_installed_languages() propagates the new list to MenuButtons."""
    # GIVEN NormCap is in capture mode (windows open)
    some_image = testcases[0].screenshot
    monkeypatch.setattr(screenshot, "capture", lambda: [some_image])
    qapp._show_windows(delay_screenshot=False)

    assert qapp.windows, "Expected at least one capture window to be open"

    # WHEN _update_installed_languages() is called with a mocked language list
    new_languages = ["deu", "sla"]
    monkeypatch.setattr(ocr.tesseract, "get_languages", lambda **_: new_languages)
    qapp._update_installed_languages()

    # THEN each open window's menu button should have the updated language list
    for window in qapp.windows.values():
        if window.menu_button is not None:
            assert window.menu_button.installed_languages == new_languages

    # AND the menu should reflect the new languages when opened
    menu_tool_btn = qapp.windows[0].findChild(QtWidgets.QToolButton, "settings_icon")
    menu_tool_btn.menu().aboutToShow.emit()
    qtbot.wait(100)
    language_group = menu_tool_btn.findChild(QtGui.QActionGroup, "language_group")
    action_names = [a.objectName() for a in language_group.children()]
    assert action_names == new_languages

    # CLEANUP: close windows so subsequent tests start with a clean state
    qapp._close_windows()
