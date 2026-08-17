"""Per-user directory resolution.

Deliberately dependency-free: `config`, `logger` and `platform` all import this,
so anything it imported back would create a cycle.
"""
import os
import sys

APP_NAME = "7DaysToBackup"


def _home() -> str:
    return os.path.expanduser("~")


def get_config_dir() -> str:
    """Per-user configuration directory.

    Note APPDATA is used rather than a Desktop/Documents-style folder because it
    is never subject to OneDrive Known Folder Move, so no Qt lookup is needed.
    """
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or _home()
    elif sys.platform.startswith("darwin"):
        base = os.path.join(_home(), "Library", "Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(_home(), ".config")
    return os.path.join(base, APP_NAME)


def get_asset(name: str) -> str:
    """Absolute path to a file in `assets/`.

    PyInstaller's one-file build unpacks the bundle into a temporary directory
    and points `sys._MEIPASS` at it, so the path differs between a source
    checkout and a frozen binary. Both are resolved here rather than at each
    call site.
    """
    base = getattr(sys, "_MEIPASS", None)
    if base is None:
        # paths.py lives at src/core/, so the repository root is two levels up.
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, "assets", name)


def get_log_dir() -> str:
    """Per-user log directory."""
    if sys.platform.startswith("win"):
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or _home()
    elif sys.platform.startswith("darwin"):
        base = os.path.join(_home(), "Library", "Logs")
    else:
        base = os.environ.get("XDG_STATE_HOME") or os.path.join(
            _home(), ".local", "state"
        )
    return os.path.join(base, APP_NAME)
