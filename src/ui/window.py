import contextlib
import os
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.core import operations
from src.core.config import config
from src.core.logger import logger
from src.core.platform import get_desktop_path, get_saves_path
from src.i18n.languages import LANGUAGES
from src.ui.settings_dialog import SettingsDialog
from src.ui.theme import create_dark_palette
from src.ui.workers import Worker


class SaveManagerWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.lang_display = {"tr": "Türkçe", "en": "English"}
        stored_lang = config.get("language", "tr")
        self.lang_code = stored_lang if stored_lang in LANGUAGES else "tr"
        self.translations = LANGUAGES[self.lang_code]
        self.resize(640, 480)

        # Held so the worker and its dialog are not garbage collected mid-run.
        self._active_worker: Worker | None = None
        self._active_dialog: QProgressDialog | None = None

        QApplication.instance().setPalette(create_dark_palette())
        self._setup_ui()
        self.load_maps()

    # ------------------------------------------------------------------ setup

    def _setup_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Header: Settings button + Language selector
        self.settings_button = QPushButton()
        self.settings_button.setFixedWidth(30)
        self.settings_button.clicked.connect(self.open_settings)

        self.language_box = QComboBox()
        for code, display in self.lang_display.items():
            self.language_box.addItem(display, code)
        self.language_box.setCurrentText(self.lang_display[self.lang_code])
        self.language_box.currentIndexChanged.connect(self.change_language)

        header_layout = QHBoxLayout()
        header_layout.addWidget(self.settings_button)
        header_layout.addStretch()
        header_layout.addWidget(self.language_box)
        main_layout.addLayout(header_layout)

        grid_layout = QGridLayout()
        main_layout.addLayout(grid_layout)

        self.map_label = QLabel()
        self.map_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        grid_layout.addWidget(self.map_label, 0, 0)

        self.save_label = QLabel()
        self.save_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        grid_layout.addWidget(self.save_label, 0, 1)

        self.map_list = QListWidget()
        self.map_list.itemSelectionChanged.connect(self.load_saves)
        grid_layout.addWidget(self.map_list, 1, 0)

        self.save_list = QListWidget()
        grid_layout.addWidget(self.save_list, 1, 1)

        self.backup_button = QPushButton()
        self.backup_button.clicked.connect(self.backup_save)
        grid_layout.addWidget(self.backup_button, 2, 0, 1, 2)

        self.delete_button = QPushButton()
        self.delete_button.clicked.connect(self.delete_save)
        grid_layout.addWidget(self.delete_button, 3, 0, 1, 2)

        self.export_button = QPushButton()
        self.export_button.clicked.connect(self.export_save)
        grid_layout.addWidget(self.export_button, 4, 0)

        self.import_button = QPushButton()
        self.import_button.clicked.connect(self.import_save)
        grid_layout.addWidget(self.import_button, 4, 1)

        # Shown in place of a modal when the saves folder cannot be found, so
        # startup is never blocked by a dialog the user cannot act on yet.
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #e08f8f;")
        self.status_label.hide()
        main_layout.addWidget(self.status_label)

        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setRowStretch(1, 1)

        self._retranslate_ui()

    def _retranslate_ui(self) -> None:
        """Single source of truth for every translatable string in this window.

        Previously _setup_ui and change_language each set widget text by hand,
        and the settings button was already missing from the second list.
        """
        t = self.translations
        self.setWindowTitle(t["title"])
        self.settings_button.setText(t["settings"])
        self.map_label.setText(t["map_list"])
        self.save_label.setText(t["save_list"])
        self.backup_button.setText(t["backup"])
        self.delete_button.setText(t["delete"])
        self.export_button.setText(t["export"])
        self.import_button.setText(t["import"])

    def change_language(self, _index: int) -> None:
        code = self.language_box.currentData()
        if not code or code not in LANGUAGES:
            return
        self.lang_code = code
        self.translations = LANGUAGES[self.lang_code]
        config.set("language", self.lang_code)
        self._retranslate_ui()
        self.load_maps()

    def open_settings(self) -> None:
        dialog = SettingsDialog(self, self.lang_code)
        if dialog.exec():
            self.load_maps()

    # ------------------------------------------------------------------ lists

    def load_maps(self) -> None:
        self.map_list.clear()
        saves_path = get_saves_path()
        if not os.path.isdir(saves_path):
            self.status_label.setText(
                self.translations["saves_missing"].format(saves_path)
            )
            self.status_label.show()
            self.save_list.clear()
            return

        self.status_label.hide()
        # scandir carries the directory-entry type, avoiding a stat per entry.
        with os.scandir(saves_path) as entries:
            names = sorted(entry.name for entry in entries if entry.is_dir())
        self.map_list.addItems(names)

    def load_saves(self) -> None:
        self.save_list.clear()
        selected_map = self._selected_map()
        if not selected_map:
            return
        saves_path = os.path.join(get_saves_path(), selected_map)
        if not os.path.isdir(saves_path):
            return
        with os.scandir(saves_path) as entries:
            names = sorted(entry.name for entry in entries)
        self.save_list.addItems(names)

    # ------------------------------------------------------------- operations

    def _run_operation(
        self,
        fn: Callable[..., Any],
        args: tuple[Any, ...],
        progress_text: str,
        success_text: str,
        error_text: str,
        cancellable: bool = True,
    ) -> None:
        """Run `fn` on the thread pool behind a progress dialog.

        The event loop keeps running for the duration, so the window repaints,
        stays responsive, and can be cancelled instead of being force-killed.
        """
        worker = Worker(fn, *args)
        dialog = QProgressDialog(
            progress_text, self.translations["cancel"], 0, 100, self
        )
        dialog.setWindowTitle(self.translations["title"])
        dialog.setWindowModality(Qt.WindowModal)
        dialog.setMinimumDuration(0)
        dialog.setAutoClose(False)
        dialog.setAutoReset(False)
        dialog.setValue(0)
        if not cancellable:
            dialog.setCancelButton(None)

        def on_progress(done: int, total: int) -> None:
            dialog.setValue(int(done / total * 100) if total else 100)

        def finish() -> None:
            if cancellable:
                # Already-disconnected raises; closing below would otherwise
                # re-emit canceled and cancel an already-finished worker.
                with contextlib.suppress(RuntimeError, TypeError):
                    dialog.canceled.disconnect()
            dialog.close()
            self._active_worker = None
            self._active_dialog = None
            self._set_actions_enabled(True)
            self.load_saves()

        def on_finished() -> None:
            finish()
            self._show_info(self.translations["title"], success_text)

        def on_cancelled() -> None:
            finish()
            self._show_info(self.translations["title"], self.translations["cancelled"])

        def on_failed(message: str) -> None:
            finish()
            logger.error("%s: %s", error_text, message)
            self._show_error(self.translations["title"], f"{error_text} - {message}")

        worker.signals.progress.connect(on_progress)
        worker.signals.finished.connect(on_finished)
        worker.signals.cancelled.connect(on_cancelled)
        worker.signals.failed.connect(on_failed)
        if cancellable:
            dialog.canceled.connect(worker.cancel)

        self._active_worker = worker
        self._active_dialog = dialog
        self._set_actions_enabled(False)
        dialog.show()
        QThreadPool.globalInstance().start(worker)

    def _set_actions_enabled(self, enabled: bool) -> None:
        for button in (
            self.backup_button,
            self.delete_button,
            self.export_button,
            self.import_button,
            self.settings_button,
        ):
            button.setEnabled(enabled)

    def backup_save(self) -> None:
        try:
            _, _, source_path = self._selected_paths()
        except ValueError as exc:
            self._show_error(self.translations["title"], str(exc))
            return

        destination_path = operations.unique_path(
            f"{source_path}_backup_{operations.timestamp_suffix()}"
        )
        logger.info("Backup %s -> %s", source_path, destination_path)
        self._run_operation(
            operations.copy_save,
            (source_path, destination_path),
            self.translations["backup_progress"],
            self.translations["backup_success"],
            self.translations["backup_error"],
        )

    def delete_save(self) -> None:
        try:
            _, selected_save, source_path = self._selected_paths()
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
        if confirm != QMessageBox.Yes:
            return

        logger.info("Delete %s", source_path)
        self._run_operation(
            operations.delete_save,
            (source_path,),
            self.translations["delete_progress"],
            self.translations["delete_success"],
            self.translations["delete_error"],
            # Stopping a delete halfway would leave a partially removed save.
            cancellable=False,
        )

    def export_save(self) -> None:
        try:
            _, selected_save, source_path = self._selected_paths()
        except ValueError as exc:
            self._show_error(self.translations["title"], str(exc))
            return

        export_dir = get_desktop_path()
        if not os.path.isdir(export_dir):
            export_dir = os.path.expanduser("~")
        # Timestamped, like backups are: the old fixed name silently truncated
        # any previous export of the same save.
        zip_path = operations.unique_path(
            os.path.join(
                export_dir, f"{selected_save}_{operations.timestamp_suffix()}.zip"
            )
        )
        logger.info("Export %s -> %s", source_path, zip_path)
        self._run_operation(
            operations.export_save,
            (source_path, zip_path),
            self.translations["export_progress"],
            self.translations["export_success"].format(zip_path),
            self.translations["export_error"].format(""),
        )

    def import_save(self) -> None:
        selected_map = self._selected_map()
        if not selected_map:
            self._show_error(
                self.translations["title"], self.translations["selection_error"]
            )
            return

        target_map_path = os.path.join(get_saves_path(), selected_map)
        start_dir = get_desktop_path()
        zip_path, _ = QFileDialog.getOpenFileName(
            self,
            self.translations["import_select"],
            start_dir if os.path.isdir(start_dir) else os.path.expanduser("~"),
            "Zip files (*.zip)",
        )
        if not zip_path:
            return

        # Validated up front so a colliding or oversized archive is refused
        # before a single byte is written.
        try:
            conflicts = operations.archive_conflicts(zip_path, target_map_path)
        except Exception as exc:  # noqa: BLE001
            self._show_error(
                self.translations["title"],
                self.translations["import_error"].format(exc),
            )
            return

        if conflicts:
            self._show_error(
                self.translations["title"],
                self.translations["import_exists"] + "\n" + "\n".join(conflicts),
            )
            return

        logger.info("Import %s -> %s", zip_path, target_map_path)
        self._run_operation(
            operations.import_save,
            (zip_path, target_map_path),
            self.translations["import_progress"],
            self.translations["import_success"],
            self.translations["import_error"].format(""),
        )

    # ---------------------------------------------------------------- helpers

    def _selected_map(self) -> str | None:
        current_item = self.map_list.currentItem()
        return current_item.text() if current_item else None

    def _selected_paths(self) -> tuple[str, str, str]:
        selected_map = self._selected_map()
        save_item = self.save_list.currentItem()

        if not selected_map or not save_item:
            raise ValueError(self.translations["selection_error"])

        selected_save = save_item.text()
        source_path = os.path.join(get_saves_path(), selected_map, selected_save)
        return selected_map, selected_save, source_path

    def _show_info(self, title: str, message: str) -> None:
        QMessageBox.information(self, title, message)

    def _show_error(self, title: str, message: str) -> None:
        QMessageBox.critical(self, title, message)
