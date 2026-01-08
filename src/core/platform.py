import os
import platform

def get_os_type() -> str:
    """İşletim sistemini tespit eder."""
    system = platform.system()
    if system == "Windows":
        return "windows"
    elif system == "Darwin":
        return "macos"
    elif system == "Linux":
        return "linux"
    else:
        return "unknown"


def get_saves_path() -> str:
    """İşletim sistemine göre 7 Days to Die save klasörünü döndürür."""
    os_type = get_os_type()
    home = os.path.expanduser("~")
    
    if os_type == "windows":
        return os.path.expandvars(r"%APPDATA%\7DaysToDie\Saves")
    elif os_type == "macos":
        return os.path.join(home, "Library", "Application Support", "7DaysToDie", "Saves")
    elif os_type == "linux":
        return os.path.join(home, ".local", "share", "7DaysToDie", "Saves")
    else:
        # Bilinmeyen işletim sistemi için varsayılan olarak Linux yolunu kullan
        return os.path.join(home, ".local", "share", "7DaysToDie", "Saves")


def get_desktop_path() -> str:
    """İşletim sistemine göre masaüstü yolunu döndürür."""
    os_type = get_os_type()
    home = os.path.expanduser("~")
    
    if os_type == "windows":
        # Windows'ta USERPROFILE\Desktop kullanılır
        return os.path.join(home, "Desktop")
    elif os_type == "macos":
        return os.path.join(home, "Desktop")
    elif os_type == "linux":
        # Linux'ta XDG_DESKTOP_DIR varsa onu kullan, yoksa ~/Desktop
        xdg_desktop = os.environ.get("XDG_DESKTOP_DIR")
        if xdg_desktop and os.path.isdir(xdg_desktop):
            return xdg_desktop
        return os.path.join(home, "Desktop")
    else:
        return os.path.join(home, "Desktop")


# İşletim sistemine göre yolları belirle
SAVES_PATH = get_saves_path()
DESKTOP_PATH = get_desktop_path()
