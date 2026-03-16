<!-- markdownlint-disable MD013 MD026 MD033 -->

# NormCap

> **This is a fork of [dynobo/normcap](https://github.com/dynobo/normcap) — a fantastic project by dynobo. Big thanks for the great work!**
>
> This fork exists because certain features were intentionally not implemented in the original project. Here, those features are added because I want them.

**_OCR powered screen-capture tool to capture information instead of images. For Linux, macOS and Windows._**

[![CI/CD](https://img.shields.io/github/actions/workflow/status/H1ghSyst3m/normcap/cicd.yaml?label=CI/CD&branch=main)](https://github.com/H1ghSyst3m/normcap/actions/workflows/cicd.yaml)
[![CodeQL](https://img.shields.io/github/actions/workflow/status/H1ghSyst3m/normcap/cicd.yaml?label=CodeQL&branch=main)](https://github.com/H1ghSyst3m/normcap/security/code-scanning/tools/CodeQL/status/)
[![GitHub Downloads](https://img.shields.io/github/downloads/H1ghSyst3m/normcap/total?label=GitHub%20downloads&color=blue)](https://github.com/H1ghSyst3m/normcap/releases)
[![AUR](https://img.shields.io/aur/votes/normcap?label=AUR%20votes&color=blue)](https://aur.archlinux.org/packages/normcap)

**Links:** [Source Code](https://github.com/H1ghSyst3m/normcap) |
[Documentation](https://github.com/H1ghSyst3m/normcap/tree/main/docs) |
[Releases](https://github.com/H1ghSyst3m/normcap/releases) |
[Changelog](https://github.com/H1ghSyst3m/normcap/blob/main/CHANGELOG)

[![Screencast](https://user-images.githubusercontent.com/11071876/189767585-8bc45c18-8392-411d-84dc-cef1cb5dbc47.gif)](https://raw.githubusercontent.com/H1ghSyst3m/normcap/main/assets/normcap.gif)

## What's different in this fork

- **New settings dialogue** — redesigned settings UI with more options (all platforms)
- **Autostart** *(Windows only)* — NormCap can be configured to start automatically with Windows
- **Global hotkeys** *(Windows only)* — trigger captures from anywhere using a configurable global keyboard shortcut

### Autostart (Windows only)

NormCap can be set to launch automatically when Windows starts. This can be enabled directly in the settings dialogue. When autostart is active, NormCap launches silently into the system tray without triggering a capture — ready to use whenever you need it.

### Global Hotkeys (Windows only)

A global keyboard shortcut can be configured to trigger a capture from any application, without needing to switch to NormCap first. The hotkey can be set and changed in the settings dialogue.

## Installation

### Python package

Install via pip for **Python >= 3.10**. Requires [Tesseract >= 5.0](https://tesseract-ocr.github.io/tessdoc/#5xx).

#### Linux

```sh
# Ubuntu/Debian
sudo apt install build-essential tesseract-ocr tesseract-ocr-eng libtesseract-dev libleptonica-dev
# Wayland: sudo apt install wl-clipboard
# X11:     sudo apt install xclip

# Arch
sudo pacman -S tesseract tesseract-data-eng
# Wayland: sudo pacman -S wl-clipboard
# X11:     sudo pacman -S xclip

# Fedora
sudo dnf install tesseract
# Wayland: sudo dnf install wl-clipboard
# X11:     sudo dnf install xclip

# openSUSE
sudo zypper install python3-devel tesseract-ocr tesseract-ocr-devel
# Wayland: sudo zypper install wl-clipboard
# X11:     sudo zypper install xclip

pip install normcap
normcap
```

#### macOS

```sh
brew install tesseract tesseract-lang
pip install normcap
normcap
```

> **macOS note:** Allow the unsigned app on first start via "System Preferences" → "Security & Privacy" → "General" → "Open anyway", and grant screenshot permission.

#### Windows

1. Install **Tesseract 5** via the [UB Mannheim installer](https://github.com/UB-Mannheim/tesseract/wiki).
2. Add the Tesseract folder (e.g. `C:\Program Files\Tesseract-OCR`) to `PATH` and set `TESSDATA_PREFIX` to the same path.
3. Verify with `tesseract --list-langs` in a new terminal.

```bash
pip install normcap
normcap
```

## Development

Prerequisites: [**uv**](https://docs.astral.sh/uv/getting-started/installation/) and [**Tesseract >= 5.0**](https://tesseract-ocr.github.io/tessdoc/#5xx).

```sh
git clone https://github.com/H1ghSyst3m/normcap.git
cd normcap
uv sync
uv run prek install
uv run python -m normcap
```

## Credits

Libraries:

- [pyside6](https://pypi.org/project/PySide6/) — Qt UI Framework bindings

External tools:

- [tesseract](https://github.com/tesseract-ocr/tesseract) — OCR engine
- [zxing-cpp](https://github.com/zxing-cpp/zxing-cpp) — QR & barcode detection
- [wl-clipboard](https://github.com/bugaevc/wl-clipboard) — Wayland clipboard utilities
- [xclip](https://github.com/astrand/xclip) — X11 clipboard CLI
- [briefcase](https://pypi.org/project/briefcase/) — standalone app packaging

## Why "NormCap"?

See [XKCD](https://xkcd.com/2116/):

[![Comic](https://imgs.xkcd.com/comics/norm_normal_file_format.png)](https://xkcd.com/2116/)

## Contributors

<a href="https://github.com/H1ghSyst3m/normcap/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=H1ghSyst3m/normcap" />
</a>

<small>Made with [contrib.rocks](https://contrib.rocks)</small>
