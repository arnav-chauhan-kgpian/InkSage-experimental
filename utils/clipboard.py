"""
InkSage Clipboard Utility
=========================

A robust wrapper for system clipboard operations.
Handles text setting, getting, and simulated pasting via keyboard injection.
"""

import sys
import time
from typing import Optional, Any, Callable
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# Try to import pynput for physical key simulation
try:
    from pynput.keyboard import Key, Controller
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    print("⚠️ pynput not available. Auto-paste will not function.")


class ClipboardManager:
    """
    Manages clipboard operations with retry logic and keyboard simulation.
    """
    
    def __init__(self):
        self.app = QApplication.instance()
        self.clipboard = self.app.clipboard() if self.app else None
        self.keyboard = Controller() if PYNPUT_AVAILABLE else None
        
        # Platform-specific paste key (Cmd for Mac, Ctrl for Windows/Linux)
        self.modifier = Key.cmd if sys.platform == 'darwin' else Key.ctrl

    def _retry_op(self, func: Callable, retries: int = 3) -> Any:
        """Retry a clipboard operation if the system resource is locked."""
        for _ in range(retries):
            try:
                return func()
            except Exception:
                time.sleep(0.05)
        return None

    def get_text(self) -> str:
        """Safe retrieval of clipboard text."""
        if not self.clipboard:
            return ""
        
        res = self._retry_op(lambda: self.clipboard.text())
        return res if res else ""

    def set_text(self, text: str) -> bool:
        """Safe setting of clipboard text."""
        if not self.clipboard:
            return False
            
        def _set():
            self.clipboard.setText(text)
            return True
            
        return self._retry_op(_set) or False

    def insert_text(self, text: str):
        """
        Copies text to clipboard and simulates a Paste (Ctrl+V) keystroke.
        """
        if not self.keyboard or not text:
            return

        # 1. Put text in clipboard
        self.set_text(text)
        
        # 2. Wait briefly for OS to register clipboard update
        time.sleep(0.1)
        
        # 3. Simulate Paste
        try:
            self.keyboard.press(self.modifier)
            self.keyboard.press('v')
            self.keyboard.release('v')
            self.keyboard.release(self.modifier)
        except Exception as e:
            print(f"❌ Failed to simulate paste: {e}")

# Global instance for easy import
clipboard_manager = ClipboardManager()