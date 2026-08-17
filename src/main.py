import os
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from src.core.logger import setup_logging
from src.core.paths import get_asset
from src.ui.window import SaveManagerWindow


def _app_icon() -> QIcon:
    """Window and taskbar icon.

    Several sizes are added to one QIcon so the window manager picks the right
    one instead of scaling a single bitmap. A missing or unreadable file is not
    fatal: an icon is cosmetic, and refusing to start over one would be worse
    than starting without it.
    """
    icon = QIcon()
    for size in (16, 32, 64, 128, 256):
        path = get_asset(f"icon-{size}.png")
        if os.path.isfile(path):
            icon.addFile(path)
    return icon


def main() -> None:
    setup_logging()
    app = QApplication(sys.argv)
    app.setApplicationName("7DaysToBackup")
    app.setWindowIcon(_app_icon())
    window = SaveManagerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
