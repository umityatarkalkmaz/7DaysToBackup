import sys

from PySide6.QtWidgets import QApplication

from src.core.logger import setup_logging
from src.ui.window import SaveManagerWindow


def main() -> None:
    setup_logging()
    app = QApplication(sys.argv)
    app.setApplicationName("7DaysToBackup")
    window = SaveManagerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
