"""Standalone settings dialog for NormCap."""

import html
import sys

from PySide6 import QtCore, QtGui, QtWidgets

from normcap import __version__
from normcap.gui.localization import _
from normcap.gui.settings_defs import (
    APPLICATION_LINKS,
    DETECTION_SECTION,
    POSTPROCESSING_SECTION,
    SETTINGS_SECTION,
)
from normcap.system import info

_DIALOG_STYLE = """
QDialog {
    background-color: #1e1e1e;
    color: white;
}
QScrollArea, QWidget#content_widget {
    background-color: transparent;
    border: none;
}
QLabel {
    color: white;
    background-color: transparent;
}
QCheckBox {
    color: white;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid rgba(255,255,255,0.4);
    background-color: rgba(255,255,255,0.05);
}
QCheckBox::indicator:checked {
    background-color: $COLOR;
    border: 1px solid $COLOR;
}
QCheckBox::indicator:hover {
    border: 1px solid rgba(255,255,255,0.7);
}
QPushButton {
    background-color: rgba(255,255,255,0.1);
    color: white;
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 4px;
    padding: 4px 12px;
}
QPushButton:hover {
    background-color: rgba(150,150,150,0.5);
    border: 1px solid rgba(255,255,255,0.4);
}
QPushButton:default {
    background-color: $COLOR;
    border: 1px solid $COLOR;
    color: white;
}
QPushButton:default:hover {
    background-color: rgba(150,150,150,0.5);
}
QKeySequenceEdit {
    background: transparent;
    border: none;
    padding: 0px;
}
QKeySequenceEdit QLineEdit {
    background-color: rgba(255,255,255,0.08);
    color: white;
    border: 1px solid rgba(255,255,255,0.25);
    border-radius: 4px;
    padding: 2px 6px;
    min-width: 120px;
}
QKeySequenceEdit QLineEdit:focus {
    border: 1px solid $COLOR;
    background-color: rgba(255,255,255,0.12);
}
QToolTip {
    background-color: rgba(50,50,50,1);
    color: white;
    border: 1px solid rgba(255,255,255,0.2);
}
QFrame[frameShape="4"],
QFrame[frameShape="5"] {
    background-color: rgba(255,255,255,0.15);
    border: none;
    max-height: 1px;
}
"""


class Communicate(QtCore.QObject):
    """SettingsDialog's communication bus."""

    on_open_url = QtCore.Signal(str)
    on_manage_languages = QtCore.Signal()
    on_show_introduction = QtCore.Signal()


class SettingsDialog(QtWidgets.QDialog):
    """Standalone settings dialog that renders all settings as native Qt widgets."""

    _section_font = QtGui.QFont(QtGui.QFont().family(), pointSize=10, weight=600)

    def __init__(
        self,
        settings: QtCore.QSettings,
        installed_languages: list[str],
        show_language_manager: bool = False,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent)

        self.settings = settings
        self.installed_languages = installed_languages
        self.has_language_manager = show_language_manager

        # L10N: Title of Settings dialog
        self.setWindowTitle(_("NormCap Settings"))
        self.setWindowIcon(QtGui.QIcon(":normcap"))
        self.setMinimumSize(400, 500)
        self.setModal(False)

        self.com = Communicate(parent=self)
        self._language_checkboxes: list[QtWidgets.QCheckBox] = []
        self._languages_layout: QtWidgets.QVBoxLayout | None = None
        self._hotkey_edit: QtWidgets.QKeySequenceEdit | None = None
        self._autostart_checkbox: QtWidgets.QCheckBox | None = None

        if hasattr(self.settings, "com"):
            self.settings.com.on_value_changed.connect(self._on_settings_value_changed)

        self.setStyleSheet(_DIALOG_STYLE.replace("$COLOR", self._get_accent_color()))

        scroll_area = self._build_scroll_area()

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 12)
        main_layout.setSpacing(0)
        main_layout.addWidget(scroll_area)
        main_layout.addWidget(self._build_close_button_wrapper())
        self.setLayout(main_layout)

    def _get_accent_color(self) -> str:
        """Return the current accent color string from settings."""
        color = QtGui.QColor(str(self.settings.value("color", "#FF2E88")))
        return color.name() if color.isValid() else "#FF2E88"

    def _build_scroll_area(self) -> QtWidgets.QScrollArea:
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)

        content_widget = QtWidgets.QWidget()
        content_widget.setObjectName("content_widget")
        content_layout = QtWidgets.QVBoxLayout(content_widget)
        content_layout.setSpacing(6)
        content_layout.setContentsMargins(16, 16, 16, 16)

        self._add_section_title(content_layout, _("Settings"))
        self._add_settings_section(content_layout)
        self._add_separator(content_layout)
        self._add_section_title(content_layout, _("Detection"))
        self._add_detection_section(content_layout)
        self._add_separator(content_layout)
        self._add_section_title(content_layout, _("Post-processing"))
        self._add_postprocessing_section(content_layout)
        self._add_separator(content_layout)
        self._add_section_title(content_layout, _("Languages"))
        self._add_languages_section(content_layout)
        self._add_separator(content_layout)
        self._add_section_title(content_layout, _("Application"))
        self._add_application_section(content_layout)
        content_layout.addStretch()

        scroll_area.setWidget(content_widget)
        return scroll_area

    def _build_close_button_wrapper(self) -> QtWidgets.QWidget:
        wrapper = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(wrapper)
        layout.setContentsMargins(12, 0, 12, 0)
        close_button = QtWidgets.QPushButton(_("Close"))
        close_button.setObjectName("close")
        close_button.clicked.connect(self.close)
        close_button.setDefault(True)
        close_button.setMinimumWidth(120)
        layout.addStretch()
        layout.addWidget(close_button)
        layout.addStretch()
        return wrapper

    def _add_section_title(self, layout: QtWidgets.QVBoxLayout, text: str) -> None:
        label = QtWidgets.QLabel(text)
        label.setFont(self._section_font)
        color = self._get_accent_color()
        label.setStyleSheet(f"color: {color}; padding-top: 4px;")
        layout.addWidget(label)

    @staticmethod
    def _add_separator(layout: QtWidgets.QVBoxLayout) -> None:
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        layout.addSpacing(8)
        layout.addWidget(line)
        layout.addSpacing(4)

    @staticmethod
    def _make_indented_layout() -> tuple[QtWidgets.QWidget, QtWidgets.QVBoxLayout]:
        """Return a widget+layout with left indentation for section items."""
        container = QtWidgets.QWidget()
        inner_layout = QtWidgets.QVBoxLayout(container)
        inner_layout.setContentsMargins(12, 0, 0, 0)
        inner_layout.setSpacing(4)
        return container, inner_layout

    def _add_settings_section(self, layout: QtWidgets.QVBoxLayout) -> None:
        container, inner = self._make_indented_layout()
        for defn in SETTINGS_SECTION:
            cb = QtWidgets.QCheckBox(defn.label())
            cb.setObjectName(defn.key)
            cb.setChecked(bool(self.settings.value(defn.key, type=bool)))
            cb.setToolTip(defn.tooltip())
            cb.toggled.connect(
                lambda checked, key=defn.key: self.settings.setValue(key, checked)
            )
            inner.addWidget(cb)

        if sys.platform == "win32":
            if info.is_briefcase_package():
                self._add_autostart_checkbox(inner)
            self._add_hotkey_widget(inner)
        layout.addWidget(container)

    def _add_autostart_checkbox(self, layout: QtWidgets.QVBoxLayout) -> None:
        # L10N: Checkbox in Settings section to enable autostart at Windows login
        self._autostart_checkbox = QtWidgets.QCheckBox(
            _("Start automatically at login")
        )
        self._autostart_checkbox.setObjectName("autostart")
        self._autostart_checkbox.setChecked(
            bool(self.settings.value("autostart", type=bool))
        )
        self._autostart_checkbox.setToolTip(
            _("Launch NormCap automatically when Windows starts.")
        )
        self._autostart_checkbox.toggled.connect(
            lambda checked: self.settings.setValue("autostart", checked)
        )
        layout.addWidget(self._autostart_checkbox)

    def _add_hotkey_widget(self, layout: QtWidgets.QVBoxLayout) -> None:
        row = QtWidgets.QHBoxLayout()

        label = QtWidgets.QLabel(_("Global hotkey"))
        label.setToolTip(
            _("Keyboard shortcut to trigger a capture while in the system tray.")
        )
        row.addWidget(label)

        stored = str(self.settings.value("hotkey") or "")
        self._hotkey_edit = QtWidgets.QKeySequenceEdit()
        self._hotkey_edit.setMaximumSequenceLength(1)
        self._hotkey_edit.setObjectName("hotkey")
        self._hotkey_edit.setKeySequence(self._str_to_key_sequence(stored))
        self._hotkey_edit.keySequenceChanged.connect(self._on_hotkey_changed)
        self._hotkey_edit.editingFinished.connect(self._on_hotkey_editing_finished)
        row.addWidget(self._hotkey_edit)

        # L10N: Button in Settings section to clear the global hotkey
        clear_btn = QtWidgets.QPushButton(_("Clear"))
        clear_btn.setObjectName("hotkey_clear")
        clear_btn.clicked.connect(self._hotkey_edit.clear)
        row.addWidget(clear_btn)

        layout.addLayout(row)

    @staticmethod
    def _str_to_key_sequence(hotkey: str) -> QtGui.QKeySequence:
        """Convert a lowercase-plus hotkey string to a ``QKeySequence``.

        Args:
            hotkey: Hotkey string, e.g. ``"ctrl+shift+j"``.

        Returns:
            Corresponding ``QKeySequence``.
        """
        if not hotkey:
            return QtGui.QKeySequence()
        return QtGui.QKeySequence.fromString(
            hotkey, QtGui.QKeySequence.SequenceFormat.PortableText
        )

    @staticmethod
    def _key_sequence_to_str(key_sequence: QtGui.QKeySequence) -> str:
        """Convert a ``QKeySequence`` to the lowercase-plus storage format.

        Args:
            key_sequence: The key sequence to convert.

        Returns:
            Hotkey string, e.g. ``"ctrl+shift+j"``, or ``""`` if empty.
        """
        if key_sequence.isEmpty():
            return ""
        return key_sequence.toString(
            QtGui.QKeySequence.SequenceFormat.PortableText
        ).lower()

    @QtCore.Slot(QtGui.QKeySequence)
    def _on_hotkey_changed(self, key_sequence: QtGui.QKeySequence) -> None:
        hotkey_str = self._key_sequence_to_str(key_sequence)
        self.settings.setValue("hotkey", hotkey_str)

    @QtCore.Slot()
    def _on_hotkey_editing_finished(self) -> None:
        if self._hotkey_edit is not None:
            self._hotkey_edit.clearFocus()

    def _add_detection_section(self, layout: QtWidgets.QVBoxLayout) -> None:
        self._detection_checkboxes: list[QtWidgets.QCheckBox] = []
        container, inner = self._make_indented_layout()
        for defn in DETECTION_SECTION:
            cb = QtWidgets.QCheckBox(defn.label())
            cb.setObjectName(defn.key)
            cb.setChecked(bool(self.settings.value(defn.key, type=bool)))
            cb.setToolTip(defn.tooltip())
            cb.toggled.connect(
                lambda checked, key=defn.key, c=cb: self._on_detection_toggled(
                    key, checked, c
                )
            )
            self._detection_checkboxes.append(cb)
            inner.addWidget(cb)

        if self._detection_checkboxes and not any(
            cb.isChecked() for cb in self._detection_checkboxes
        ):
            first_cb = self._detection_checkboxes[0]
            first_cb.blockSignals(True)
            first_cb.setChecked(True)
            first_cb.blockSignals(False)
            self.settings.setValue(first_cb.objectName(), True)
        layout.addWidget(container)

    def _on_detection_toggled(
        self, key: str, checked: bool, cb: QtWidgets.QCheckBox
    ) -> None:
        """Ensure at least one detection method is always selected."""
        if not checked and not any(c.isChecked() for c in self._detection_checkboxes):
            cb.blockSignals(True)
            cb.setChecked(True)
            cb.blockSignals(False)
            self.settings.setValue(key, True)
            return
        self.settings.setValue(key, checked)

    def _add_postprocessing_section(self, layout: QtWidgets.QVBoxLayout) -> None:
        container, inner = self._make_indented_layout()
        for defn in POSTPROCESSING_SECTION:
            cb = QtWidgets.QCheckBox(defn.label())
            cb.setObjectName(defn.key)
            cb.setChecked(bool(self.settings.value(defn.key, type=bool)))
            cb.setToolTip(defn.tooltip())
            cb.toggled.connect(
                lambda checked, key=defn.key: self.settings.setValue(key, checked)
            )
            inner.addWidget(cb)
        layout.addWidget(container)

    def _add_languages_section(self, layout: QtWidgets.QVBoxLayout) -> None:
        languages_container = QtWidgets.QWidget()
        self._languages_layout = QtWidgets.QVBoxLayout(languages_container)
        self._languages_layout.setContentsMargins(12, 0, 0, 0)
        self._languages_layout.setSpacing(4)
        layout.addWidget(languages_container)
        self._populate_language_section()

    def _populate_language_section(self) -> None:
        if self._languages_layout is None:
            return
        while self._languages_layout.count():
            item = self._languages_layout.takeAt(0)
            if item.widget():
                w = item.widget()
                w.setParent(None)
                w.deleteLater()
        self._language_checkboxes = []

        stored = self.settings.value("language")
        if isinstance(stored, (list, tuple)):
            active_languages = [str(lang) for lang in stored]
        elif stored is None:
            active_languages = []
        else:
            active_languages = [str(stored)]

        for language in self.installed_languages:
            cb = QtWidgets.QCheckBox(language)
            cb.setObjectName(f"lang_{language}")
            cb.setChecked(language in active_languages)
            cb.toggled.connect(
                lambda _, lang=language, c=cb: self._on_language_toggled(lang, c)
            )
            self._language_checkboxes.append(cb)
            self._languages_layout.addWidget(cb)

        if self.has_language_manager:
            # L10N: Button in Languages section (prebuilt package).
            manage_btn = QtWidgets.QPushButton(_("add/remove …"))
            manage_btn.setObjectName("manage_languages")
            manage_btn.clicked.connect(self.com.on_manage_languages.emit)
            self._languages_layout.addWidget(manage_btn)
        else:
            # L10N: Label in Languages section (Python package).
            need_more_label = QtWidgets.QLabel(
                "<a href='#'>" + _("… need more?") + "</a>"
            )
            need_more_label.setObjectName("show_help_languages")
            need_more_label.linkActivated.connect(self._on_need_more_languages)
            self._languages_layout.addWidget(need_more_label)

    def refresh_languages(self, installed_languages: list[str]) -> None:
        """Rebuild the language section with an updated list of installed languages."""
        self.installed_languages = installed_languages
        self._populate_language_section()

    @QtCore.Slot(str, object)
    def _on_settings_value_changed(self, key: str, value: object) -> None:
        """Sync dialog widgets when settings change externally.

        Handles synchronization for ``"language"`` (updates language checkboxes)
        and ``"hotkey"`` (updates the ``QKeySequenceEdit`` widget on Windows).
        """
        if key == "language":
            values = value if isinstance(value, (list, tuple)) else [value]
            active = [str(v) for v in values]
            for cb in self._language_checkboxes:
                lang = cb.objectName().removeprefix("lang_")
                cb.blockSignals(True)
                cb.setChecked(lang in active)
                cb.blockSignals(False)
        elif key == "hotkey" and self._hotkey_edit is not None:
            self._hotkey_edit.blockSignals(True)
            self._hotkey_edit.setKeySequence(
                self._str_to_key_sequence(str(value or ""))
            )
            self._hotkey_edit.blockSignals(False)
        elif key == "autostart" and self._autostart_checkbox is not None:
            self._autostart_checkbox.blockSignals(True)
            self._autostart_checkbox.setChecked(bool(value))
            self._autostart_checkbox.blockSignals(False)

    @QtCore.Slot()
    def _on_need_more_languages(self) -> None:
        message_box = QtWidgets.QMessageBox(parent=self)
        message_box.setIconPixmap(QtGui.QIcon(":normcap").pixmap(48, 48))
        message_box.setText(
            # L10N: Message box shown in Python package when trying to install language
            _(
                "This installation of NormCap uses the Tesseract binary installed "
                "on your system. To install additional languages, please refer to "
                "the documentation of that Tesseract installation."
            )
        )
        message_box.exec()

    def _on_language_toggled(self, language: str, cb: QtWidgets.QCheckBox) -> None:
        """Ensure at least one language is always selected."""
        languages = [
            c.objectName().removeprefix("lang_")
            for c in self._language_checkboxes
            if c.isChecked()
        ]
        if not languages:
            cb.blockSignals(True)
            cb.setChecked(True)
            cb.blockSignals(False)
            languages = [language]
        self.settings.setValue("language", languages)

    def _add_application_section(self, layout: QtWidgets.QVBoxLayout) -> None:
        container, inner = self._make_indented_layout()
        color = self._get_accent_color()

        version_label = QtWidgets.QLabel(f"NormCap v{__version__}")
        version_label.setObjectName("version_label")
        version_label.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 11px;")
        inner.addWidget(version_label)

        intro_btn = QtWidgets.QPushButton(_("Introduction"))
        intro_btn.setObjectName("show_introduction")
        intro_btn.clicked.connect(self.com.on_show_introduction.emit)
        inner.addWidget(intro_btn)

        for label_fn, url in APPLICATION_LINKS:
            safe_url = html.escape(url)
            safe_text = html.escape(label_fn())
            label = QtWidgets.QLabel(
                f"<a href='{safe_url}' style='color: {color};'>{safe_text}</a>"
            )
            label.setOpenExternalLinks(False)
            label.linkActivated.connect(self.com.on_open_url.emit)
            inner.addWidget(label)

        layout.addWidget(container)
