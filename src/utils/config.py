"""
InkSage Configuration Manager
=============================

A Singleton utility that loads `settings.yaml` and provides safe,
dot-notation access to configuration values across the application.
"""

import yaml
from pathlib import Path
from typing import Any, Dict, Optional

# Define path relative to this file location
# src/utils/config.py -> src/utils -> src -> [ROOT] -> config/settings.yaml
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "settings.yaml"

class Config:
    """
    Singleton Configuration Manager.
    Loads settings.yaml and provides safe access methods.
    """
    _instance: Optional['Config'] = None
    _data: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self):
        """Loads the YAML file into memory."""
        self._data = {}
        
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    self._data = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"❌ Error loading config: {e}")
        else:
            print(f"⚠️ Config not found at {CONFIG_PATH}. Using internal defaults.")
            self._data = {}

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Access nested config using dot notation.
        Example: config.get('ui.colors.primary', '#000000')
        """
        keys = key_path.split('.')
        value = self._data
        
        try:
            for k in keys:
                if not isinstance(value, dict):
                    return default
                value = value.get(k)
                if value is None:
                    return default
            return value
        except (KeyError, TypeError, AttributeError):
            return default

    def get_role_prompt(self, role_name: str) -> str:
        """
        Helper for Context Awareness. Retrieves the system prompt for a specific role.
        """
        # 1. Try specific role
        roles = self.get('context_awareness.roles', {})
        if role_name in roles:
            return roles[role_name].get('system_prompt', "")
            
        # 2. Fallback to default role defined in config
        default_role = self.get('context_awareness.default_role', 'general')
        if role_name != default_role and default_role in roles:
             return roles[default_role].get('system_prompt', "You are a helpful assistant.")
             
        # 3. Ultimate Fallback
        return "You are a helpful AI assistant."

    def set(self, key_path: str, value: Any):
        """
        Update a setting in memory (does not persist to disk).
        """
        keys = key_path.split('.')
        target = self._data
        
        for k in keys[:-1]:
            target = target.setdefault(k, {})
            
        target[keys[-1]] = value

# Global singleton instance
config = Config()