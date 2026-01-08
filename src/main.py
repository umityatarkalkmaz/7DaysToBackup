import sys
from PySide6.QtWidgets import QApplication
from src.ui.window import SaveManagerWindow

def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("7DaysToBackup")
    window = SaveManagerWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
