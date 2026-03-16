"""Dialog window with basic instructions for using NormCap.

Some users are confused about how NormCap works or where to find the settings menu.
This dialog should be shown at least once on the very first start to explain those
basic features.

By toggling a checkbox, the user can opt out of showing the screen on startup.
On Windows packaged builds, an autostart checkbox is also shown in the footer.
"""

import enum
import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from normcap.gui.localization import _
from normcap.system import info


@dataclass
class Section:
    title: str
    text: str
    image: Path


class Choice(enum.IntEnum):
    """Return codes of the Dialog.

    As 0 is default for closing the Dialog (through X or shortcut), we use different
    values to distinguish between closing the dialog w/ or w/o having the dont show
    checkbox selected.
    """

    REJECTED = 0
    ACCEPTED = 1
    SHOW = 10
    DONT_SHOW = 11


class IntroductionDialog(QtWidgets.QDialog):
    def __init__(
        self,
        show_on_startup: bool,
        autostart: bool = False,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent)

        # L10N: Introduction window title
        self.setWindowTitle(_("Introduction to NormCap"))
        self.setWindowIcon(QtGui.QIcon(":normcap"))
        # On Windows a 5th section is shown; use a wider minimum to avoid
        # horizontal scroll
        min_width = 1280 if sys.platform == "win32" else 1024
        self.setMinimumSize(min_width, 650)
        self.setModal(True)

        self.autostart_checkbox: QtWidgets.QCheckBox | None = None
        if sys.platform == "win32" and info.is_briefcase_package():
            # L10N: Introduction window autostart checkbox
            self.autostart_checkbox = QtWidgets.QCheckBox(
                _("Start automatically at login")
            )
            self.autostart_checkbox.setObjectName("autostart")
            self.autostart_checkbox.setToolTip(
                _("Launch NormCap automatically when Windows starts.")
            )
            self.autostart_checkbox.setChecked(autostart)

        # L10N: Introduction window checkbox
        self.show_on_startup_checkbox = QtWidgets.QCheckBox(_("Show on startup"))
        self.show_on_startup_checkbox.setChecked(show_on_startup)
        # L10N: Introduction window button
        self.ok_button = QtWidgets.QPushButton(_("Ok"))
        self.ok_button.clicked.connect(self._on_button_clicked)
        self.ok_button.setDefault(True)

        main_vbox = QtWidgets.QVBoxLayout()
        main_vbox.addStretch()
        main_vbox.addWidget(self._create_header())
        main_vbox.addWidget(self._create_content())
        main_vbox.addLayout(self._create_footer())
        main_vbox.addStretch()
        self.setLayout(main_vbox)

    @property
    def sections_data(self) -> list[Section]:
        prefix = sys.platform
        img_path = Path(__file__).resolve().parents[1] / "resources" / "images"
        # L10N: Introduction window shortcut for pasting on Linux and Windows
        paste_shortcut_win32_linux = _("Ctrl + v")
        # L10N: Introduction window shortcut for pasting on macOS
        paste_shortcut_darwin = _("Cmd + v")

        # L10N: Introduction window step description
        settings_text = _(
            "Open the quick menu using the gear icon in the upper right "
            "corner of your screen, "
            "or use the full Settings dialog from the system tray icon for "
            "all options."
        )

        sections = [
            Section(
                title=_("1. Select area"),
                text=_(
                    "Wait until a pink border appears around your screen, then select "
                    "the desired capture area."
                ),
                image=img_path / f"{prefix}-intro-1.png",
            ),
            Section(
                title=_("2. Wait for detection"),
                text=_(
                    "Processing takes time. Wait for a notification or a color "
                    "change of the system tray icon."
                ),
                image=img_path / f"{prefix}-intro-2.png",
            ),
            Section(
                title=_("3. Paste from clipboard"),
                text=_(
                    "The detection result will be copied to your system's clipboard. "
                    "Paste it into any application ({shortcut})."
                ).format(
                    shortcut=paste_shortcut_darwin
                    if sys.platform == "darwin"
                    else paste_shortcut_win32_linux
                ),
                image=img_path / f"{prefix}-intro-3.png",
            ),
            Section(
                title=_("Settings & more"),
                text=settings_text,
                image=img_path / f"{prefix}-intro-4.png",
            ),
        ]
        if prefix == "win32":
            sections.append(
                Section(
                    title=_("Global Hotkey"),
                    text=_(
                        "Trigger a capture from anywhere using the global hotkey. "
                        "The default shortcut is Ctrl+Shift+J. "
                        "You can change it anytime in the Settings dialog. "
                        "Note: the global hotkey requires NormCap to be running "
                        "in tray mode."
                    ),
                    image=img_path / f"{prefix}-intro-5.png",
                )
            )
        return sections

    @staticmethod
    def _create_header() -> QtWidgets.QLabel:
        # L10N: Introduction window headline
        header = QtWidgets.QLabel(_("Basic Usage"))
        header_font = QtGui.QFont(QtGui.QFont().family(), pointSize=18, weight=300)
        header.setFont(header_font)
        return header

    def _create_content(self) -> QtWidgets.QWidget:
        sections_hbox = QtWidgets.QHBoxLayout()
        sections_hbox.setSpacing(15)
        sections_hbox.setContentsMargins(0, 15, 0, 15)

        for section in self.sections_data:
            section_layout = self._create_content_section(
                title=section.title, image=section.image, text=section.text
            )
            sections_hbox.addLayout(section_layout, 1)

        sections_container = QtWidgets.QWidget()
        sections_container.setLayout(sections_hbox)
        scroll = QtWidgets.QScrollArea()
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setWidget(sections_container)
        scroll.setFixedHeight(sections_container.height())
        return scroll

    @staticmethod
    def _create_content_section(
        title: str, text: str, image: Path
    ) -> QtWidgets.QLayout:
        vbox = QtWidgets.QVBoxLayout()

        section_title = QtWidgets.QLabel(title)
        section_title.setFont(QtGui.QFont(QtGui.QFont().family(), weight=600))
        section_title.setWordWrap(True)
        vbox.addWidget(section_title)

        section_text = QtWidgets.QLabel(text)
        section_text.setWordWrap(True)
        vbox.addWidget(section_text)

        vbox.addStretch()

        image_label = QtWidgets.QLabel()
        image_label.setFixedWidth(230)
        image_label.setFixedHeight(400)
        pixmap = QtGui.QPixmap(str(image.resolve()))
        if not pixmap.isNull():
            image_label.setPixmap(pixmap)
            image_label.setScaledContents(True)
        else:
            image_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            palette = image_label.palette()
            bg = palette.color(QtGui.QPalette.ColorRole.Window).name()
            border = palette.color(QtGui.QPalette.ColorRole.Mid).name()
            text_color = palette.color(QtGui.QPalette.ColorRole.PlaceholderText).name()
            image_label.setStyleSheet(
                f"background-color: {bg};"
                f" border: 1px solid {border};"
                " border-radius: 4px;"
                f" color: {text_color};"
            )
            image_label.setText(title)
        vbox.addWidget(image_label)

        return vbox

    def _create_footer(self) -> QtWidgets.QLayout:
        footer_hbox = QtWidgets.QHBoxLayout()
        footer_hbox.setContentsMargins(0, 0, 2, 0)

        if self.autostart_checkbox is not None:
            footer_hbox.addWidget(self.autostart_checkbox)
        footer_hbox.addStretch()

        footer_hbox.addWidget(self.show_on_startup_checkbox)
        footer_hbox.addWidget(self.ok_button)
        return footer_hbox

    def _on_button_clicked(self) -> None:
        return_code = (
            Choice.SHOW
            if self.show_on_startup_checkbox.isChecked()
            else Choice.DONT_SHOW
        )
        self.done(return_code)
