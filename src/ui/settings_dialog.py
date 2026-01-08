from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFileDialog, QGroupBox
)
from PySide6.QtCore import Qt
from src.core.config import config
from src.i18n.languages import LANGUAGES

class SettingsDialog(QDialog):
    def __init__(self, parent=None, lang_code="tr"):
        super().__init__(parent)
        self.lang_code = lang_code
        self.translations = LANGUAGES[self.lang_code]
        self.setWindowTitle(self.translations.get("settings_title", "Ayarlar"))
        self.resize(500, 200)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Advanced Settings Group
        adv_group = QGroupBox(self.translations.get("advanced_settings", "Gelişmiş Ayarlar"))
        adv_layout = QVBoxLayout(adv_group)
        
        # Custom Save Path
        path_label = QLabel(self.translations.get("custom_save_path_label", "Özel Save Dosyası Konumu (İsteğe Bağlı):"))
        adv_layout.addWidget(path_label)
        
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setText(config.get("custom_save_path", ""))
        self.path_input.setPlaceholderText(self.translations.get("custom_save_path_placeholder", "Otomatik algılama için boş bırakın"))
        path_layout.addWidget(self.path_input)
        
        browse_btn = QPushButton("...")
        browse_btn.setFixedWidth(30)
        browse_btn.clicked.connect(self._browse_path)
        path_layout.addWidget(browse_btn)
        
        adv_layout.addLayout(path_layout)
        
        help_label = QLabel(self.translations.get("custom_save_path_help", "Not: Bu ayar sadece oyun save dosyalarını otomatik bulamazsa kullanılmalıdır."))
        help_label.setStyleSheet("color: #888;")
        help_label.setWordWrap(True)
        adv_layout.addWidget(help_label)
        
        layout.addWidget(adv_group)
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        save_btn = QPushButton(self.translations.get("save", "Kaydet"))
        save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton(self.translations.get("cancel", "İptal"))
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
    def _browse_path(self):
        directory = QFileDialog.getExistingDirectory(self, self.translations.get("select_folder", "Klasör Seç"))
        if directory:
            self.path_input.setText(directory)
            
    def _save_settings(self):
        path = self.path_input.text().strip()
        config.set("custom_save_path", path)
        self.accept()
