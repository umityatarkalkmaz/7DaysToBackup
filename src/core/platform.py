import os
import platform

from src.core.config import config

_OS_TYPES = {"Windows": "windows", "Darwin": "macos", "Linux": "linux"}


def get_os_type() -> str:
    """İşletim sistemini tespit eder."""
    return _OS_TYPES.get(platform.system(), "unknown")


def get_default_saves_path() -> str:
    """İşletim sistemine göre varsayılan 7 Days to Die save klasörünü döndürür."""
    os_type = get_os_type()
    home = os.path.expanduser("~")

    if os_type == "windows":
        return os.path.expandvars(r"%APPDATA%\7DaysToDie\Saves")
    elif os_type == "macos":
        return os.path.join(home, "Library", "Application Support", "7DaysToDie", "Saves")
    else:
        return os.path.join(home, ".local", "share", "7DaysToDie", "Saves")


def get_saves_path() -> str:
    """Kullanıcı tanımlı veya varsayılan save klasörünü döndürür."""
    custom_path = config.get("custom_save_path", "")
    if custom_path and os.path.isdir(custom_path):
        return custom_path
    return get_default_saves_path()


def get_desktop_path() -> str:
    """İşletim sistemine göre masaüstü yolunu döndürür.

    Qt is asked first because it resolves Windows known folders properly: a
    hardcoded ~/Desktop is wrong whenever the Desktop folder is redirected by
    OneDrive Known Folder Move or localized on a non-English Windows. The
    manual join remains as a fallback so this module still works without Qt.
    """
    try:
        from PySide6.QtCore import QStandardPaths

        desktop = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DesktopLocation
        )
        if desktop and os.path.isdir(desktop):
            return desktop
    except Exception:  # noqa: BLE001 - Qt missing or unusable; fall through
        pass

    home = os.path.expanduser("~")
    if get_os_type() == "linux":
        xdg_desktop = os.environ.get("XDG_DESKTOP_DIR")
        if xdg_desktop and os.path.isdir(xdg_desktop):
            return xdg_desktop
    return os.path.join(home, "Desktop")
