import os
import platform
import shutil
import sys
import zipfile
from datetime import datetime
from typing import Optional, Tuple

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QComboBox,
)

from languages import LANGUAGES


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


def create_dark_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(35, 39, 46))
    palette.setColor(QPalette.WindowText, QColor(245, 246, 250))
    palette.setColor(QPalette.Base, QColor(42, 46, 56))
    palette.setColor(QPalette.AlternateBase, QColor(45, 49, 58))
    palette.setColor(QPalette.ToolTipBase, QColor(42, 46, 56))
    palette.setColor(QPalette.ToolTipText, QColor(245, 246, 250))
    palette.setColor(QPalette.Text, QColor(245, 246, 250))
    palette.setColor(QPalette.Button, QColor(58, 63, 75))
    palette.setColor(QPalette.ButtonText, QColor(245, 246, 250))
    palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.Highlight, QColor(68, 74, 86))
    palette.setColor(QPalette.HighlightedText, QColor(245, 246, 250))
    return palette


class SaveManagerWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.lang_code = "tr"
        self.translations = LANGUAGES[self.lang_code]
        self.lang_display = {"tr": "Türkçe", "en": "English"}
        self.setWindowTitle(self.translations["title"])
        self.resize(640, 480)

        QApplication.instance().setPalette(create_dark_palette())
        self._setup_ui()
        self.load_maps()

    def _setup_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        self.language_box = QComboBox()
        for code, display in self.lang_display.items():
            self.language_box.addItem(display, code)
        self.language_box.setCurrentText(self.lang_display[self.lang_code])
        self.language_box.currentTextChanged.connect(self.change_language)

        header_layout = QHBoxLayout()
        header_layout.addStretch()
        header_layout.addWidget(self.language_box)
        main_layout.addLayout(header_layout)

        grid_layout = QGridLayout()
        main_layout.addLayout(grid_layout)

        self.map_label = QLabel(self.translations["map_list"])
        self.map_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        grid_layout.addWidget(self.map_label, 0, 0)

        self.save_label = QLabel(self.translations["save_list"])
        self.save_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        grid_layout.addWidget(self.save_label, 0, 1)

        self.map_list = QListWidget()
        self.map_list.itemSelectionChanged.connect(self.load_saves)
        grid_layout.addWidget(self.map_list, 1, 0)

        self.save_list = QListWidget()
        grid_layout.addWidget(self.save_list, 1, 1)

        self.backup_button = QPushButton(self.translations["backup"])
        self.backup_button.clicked.connect(self.backup_save)
        grid_layout.addWidget(self.backup_button, 2, 0, 1, 2)

        self.delete_button = QPushButton(self.translations["delete"])
        self.delete_button.clicked.connect(self.delete_save)
        grid_layout.addWidget(self.delete_button, 3, 0, 1, 2)

        self.export_button = QPushButton(self.translations["export"])
        self.export_button.clicked.connect(self.export_save)
        grid_layout.addWidget(self.export_button, 4, 0)

        self.import_button = QPushButton(self.translations["import"])
        self.import_button.clicked.connect(self.import_save)
        grid_layout.addWidget(self.import_button, 4, 1)

        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setRowStretch(1, 1)

    def change_language(self, display_text: str) -> None:
        for code, display in self.lang_display.items():
            if display == display_text:
                self.lang_code = code
                break
        self.translations = LANGUAGES[self.lang_code]
        self.setWindowTitle(self.translations["title"])
        self.map_label.setText(self.translations["map_list"])
        self.save_label.setText(self.translations["save_list"])
        self.backup_button.setText(self.translations["backup"])
        self.delete_button.setText(self.translations["delete"])
        self.export_button.setText(self.translations["export"])
        self.import_button.setText(self.translations["import"])

    def load_maps(self) -> None:
        self.map_list.clear()
        if not os.path.isdir(SAVES_PATH):
            self._show_error(
                self.translations["title"],
                self.translations["saves_missing"].format(SAVES_PATH)
            )
            return

        for map_name in sorted(os.listdir(SAVES_PATH)):
            map_path = os.path.join(SAVES_PATH, map_name)
            if os.path.isdir(map_path):
                self.map_list.addItem(QListWidgetItem(map_name))

    def load_saves(self) -> None:
        self.save_list.clear()
        selected_map = self._selected_map()
        if not selected_map:
            return
        saves_path = os.path.join(SAVES_PATH, selected_map)
        if not os.path.isdir(saves_path):
            return
        for save in sorted(os.listdir(saves_path)):
            self.save_list.addItem(QListWidgetItem(save))

    def backup_save(self) -> None:
        try:
            selected_map, selected_save, source_path = self._selected_paths()
            backup_suffix = datetime.now().strftime("_backup_%Y.%m.%d-%H.%M.%S")
            destination_path = f"{source_path}{backup_suffix}"
            shutil.copytree(source_path, destination_path)
            self.load_saves()
            self._show_info(self.translations["title"], self.translations["backup_success"])
        except ValueError as exc:
            self._show_error(self.translations["title"], str(exc))
        except Exception as exc:  # noqa: BLE001
            self._show_error(self.translations["title"], f"{self.translations['backup_error']} - {exc}")

    def delete_save(self) -> None:
        try:
            selected_map, selected_save, source_path = self._selected_paths()
        except ValueError as exc:
            self._show_error(self.translations["title"], str(exc))
            return

        confirm = QMessageBox.question(
            self,
            self.translations["title"],
            self.translations["delete_confirm"].format(selected_save),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            try:
                shutil.rmtree(source_path)
                self.load_saves()
                self._show_info(self.translations["title"], self.translations["delete_success"])
            except Exception as exc:  # noqa: BLE001
                self._show_error(self.translations["title"], f"{self.translations['delete_error']} - {exc}")

    def export_save(self) -> None:
        try:
            selected_map, selected_save, source_path = self._selected_paths()
            zip_filename = f"{selected_save}.zip"
            zip_path = os.path.join(DESKTOP_PATH, zip_filename)
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for root_dir, _, files in os.walk(source_path):
                    for file in files:
                        abs_path = os.path.join(root_dir, file)
                        rel_path = os.path.relpath(abs_path, os.path.join(source_path, ".."))
                        zip_file.write(abs_path, rel_path)
            self._show_info(
                self.translations["title"], self.translations["export_success"].format(zip_path)
            )
        except ValueError as exc:
            self._show_error(self.translations["title"], str(exc))
        except Exception as exc:  # noqa: BLE001
            self._show_error(self.translations["title"], self.translations["export_error"].format(exc))

    def import_save(self) -> None:
        selected_map = self._selected_map()
        if not selected_map:
            self._show_error(self.translations["title"], self.translations["selection_error"])
            return

        target_map_path = os.path.join(SAVES_PATH, selected_map)
        zip_path, _ = QFileDialog.getOpenFileName(
            self,
            self.translations["import_select"],
            DESKTOP_PATH,
            "Zip files (*.zip)",
        )
        if not zip_path:
            return

        try:
            with zipfile.ZipFile(zip_path, "r") as zip_file:
                members = zip_file.namelist()
                if not members:
                    raise ValueError(self.translations["import_error"].format("Empty archive"))
                top_level_folder = members[0].split("/")[0]
                extract_path = os.path.join(target_map_path, top_level_folder)
                if os.path.exists(extract_path):
                    self._show_error(self.translations["title"], self.translations["import_exists"])
                    return
                zip_file.extractall(target_map_path)
            self.load_saves()
            self._show_info(self.translations["title"], self.translations["import_success"])
        except ValueError as exc:
            self._show_error(self.translations["title"], str(exc))
        except Exception as exc:  # noqa: BLE001
            self._show_error(self.translations["title"], self.translations["import_error"].format(exc))

    def _selected_map(self) -> Optional[str]:
        current_item = self.map_list.currentItem()
        return current_item.text() if current_item else None

    def _selected_paths(self) -> Tuple[str, str, str]:
        selected_map = self._selected_map()
        save_item = self.save_list.currentItem()

        if not selected_map or not save_item:
            raise ValueError(self.translations["selection_error"])

        selected_save = save_item.text()
        source_path = os.path.join(SAVES_PATH, selected_map, selected_save)
        return selected_map, selected_save, source_path

    def _show_info(self, title: str, message: str) -> None:
        QMessageBox.information(self, title, message)

    def _show_error(self, title: str, message: str) -> None:
        QMessageBox.critical(self, title, message)


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("7DaysToBackup")
    window = SaveManagerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
