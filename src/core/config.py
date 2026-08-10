import json
import os
import tempfile
from typing import Any

from src.core.logger import logger
from src.core.paths import get_config_dir

CONFIG_FILE = os.path.join(get_config_dir(), "config.json")


class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.config = {}
            cls._instance.load_config()
        return cls._instance

    def load_config(self) -> None:
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {}
        except (OSError, ValueError) as exc:
            # ValueError covers json.JSONDecodeError. A corrupt file is reported
            # rather than silently discarded.
            logger.warning("Config unreadable (%s); using defaults: %s", CONFIG_FILE, exc)
            self.config = {}

    def save_config(self) -> bool:
        """Write atomically. Returns False on failure — callers must not ignore it."""
        directory = os.path.dirname(CONFIG_FILE)
        try:
            os.makedirs(directory, exist_ok=True)
            fd, tmp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=4)
                    f.flush()
                    os.fsync(f.fileno())
                # Atomic on POSIX and Windows: an interrupted write can no longer
                # leave a truncated, unparseable config.json behind.
                os.replace(tmp_path, CONFIG_FILE)
            except BaseException:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                raise
            return True
        except OSError as exc:
            logger.exception("Failed to save config to %s: %s", CONFIG_FILE, exc)
            return False

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        self.config[key] = value
        return self.save_config()


# Global instance
config = ConfigManager()
