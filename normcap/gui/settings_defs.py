"""Shared settings metadata consumed by MenuButton and SettingsDialog."""

import sys
from dataclasses import dataclass
from typing import Callable

from normcap.gui.constants import URLS
from normcap.gui.localization import _


@dataclass(frozen=True)
class BoolSettingDef:
    """Metadata for a boolean toggle/checkbox setting."""

    key: str
    label: Callable[[], str]
    tooltip: Callable[[], str]


def _notification_tooltip() -> str:
    base = _("Show status information via your system's desktop\nnotification center.")
    if sys.platform in {"darwin", "win32"}:
        base += f"\n({_('Click on the notification to open the result')})"
    return base


SETTINGS_SECTION: list[BoolSettingDef] = [
    BoolSettingDef(
        key="notification",
        label=lambda: _("Show notification"),
        tooltip=_notification_tooltip,
    ),
    BoolSettingDef(
        key="tray",
        label=lambda: _("Keep in system tray"),
        tooltip=lambda: _(
            "Keep NormCap running in the background. Another\n"
            "capture can be triggered via the tray icon."
        ),
    ),
    BoolSettingDef(
        key="update",
        label=lambda: _("Check for update"),
        tooltip=lambda: _(
            "Frequently fetch NormCap's releases online and display\n"
            "a message if a new version is available."
        ),
    ),
]

DETECTION_SECTION: list[BoolSettingDef] = [
    BoolSettingDef(
        key="detect-text",
        label=lambda: _("Text"),
        tooltip=lambda: _("Tries to detect text in the selected region using OCR."),
    ),
    BoolSettingDef(
        key="detect-codes",
        label=lambda: _("QR && Barcodes"),
        tooltip=lambda: _(
            "Detects Barcodes and QR codes. If one or more codes are found,\n"
            "text detection (OCR) is skipped and only the codes' data is returned."
        ),
    ),
]

POSTPROCESSING_SECTION: list[BoolSettingDef] = [
    BoolSettingDef(
        key="parse-text",
        label=lambda: _("Parse text"),
        tooltip=lambda: _(
            "Tries to determine the text's type (e.g. line,\n"
            "paragraph, URL, email) and formats the output\n"
            "accordingly.\n"
            "Turn it off to return the text exactly as detected\n"
            "by the Optical Character Recognition Software."
        ),
    ),
]

APPLICATION_LINKS: list[tuple[Callable[[], str], str]] = [
    (lambda: _("Website"), URLS.website),
    (lambda: _("Source code"), URLS.github),
    (lambda: _("Releases"), URLS.releases),
    (lambda: _("Report a problem"), URLS.issues),
]
