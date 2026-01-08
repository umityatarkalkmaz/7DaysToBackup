import json
import os
from typing import Dict, Any, Optional

CONFIG_FILE = "config.json"

class ConfigManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.config = {}
            cls._instance.load_config()
        return cls._instance
    
    def load_config(self) -> None:
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except Exception:
                self.config = {}
        else:
            self.config = {}
            
    def save_config(self) -> None:
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
        except Exception:
            pass
            
    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)
        
    def set(self, key: str, value: Any) -> None:
        self.config[key] = value
        self.save_config()

# Global instance
config = ConfigManager()
