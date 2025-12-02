"""
InkSage Context Sniffer (The Chameleon)
=======================================

Monitors the active operating system window to determine the user's
current context (e.g., Coding, Writing, Emailing). This allows the
Assistant to automatically switch system prompts (Personas).
"""

import time
import threading
from typing import Optional
from PySide6.QtCore import QObject, Signal

from ..utils.config import config

# Cross-platform window title retrieval
try:
    import pygetwindow as gw
    HAS_PYGETWINDOW = True
except ImportError:
    HAS_PYGETWINDOW = False
    print("⚠️ 'pygetwindow' not installed. Context awareness will be limited.")


class ContextSniffer(QObject):
    """
    Background service that polls the OS for the active window title.
    Maps titles to specific 'Roles' defined in settings.yaml.
    """
    
    # Emits: (window_title, role_key)
    # e.g., ("main.py - Visual Studio Code", "code")
    context_changed = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.enabled = config.get('context_awareness.enabled', True)
        self.check_interval = config.get('context_awareness.check_interval', 2000) / 1000.0
        
        # Load roles from config
        self.roles_config = config.get('context_awareness.roles', {})
        self.default_role = config.get('context_awareness.default_role', 'general')
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_window_title = ""
        self._last_role = self.default_role

    def start(self):
        """Start the background monitoring thread."""
        if not self.enabled:
            return
            
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        print("🦎 Chameleon: Sniffer Active")

    def stop(self):
        """Stop monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)

    def _monitor_loop(self):
        """Main polling loop."""
        while self._running:
            try:
                current_title = self._get_active_window_title()
                
                # Check for changes (Simple string comparison first)
                if current_title and current_title != self._last_window_title:
                    self._last_window_title = current_title
                    self._process_context_change(current_title)
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                # Prevent thread death on transient OS errors
                print(f"⚠️ Context Sniffer Error: {e}")
                time.sleep(1)

    def _process_context_change(self, window_title: str):
        """
        Determine the role based on keywords in the title.
        """
        detected_role = self.default_role
        window_title_lower = window_title.lower()

        # Iterate through config roles (code, professional, creative)
        for role_key, role_data in self.roles_config.items():
            apps = role_data.get('apps', [])
            
            # Check if any app keyword matches the window title
            match_found = False
            for app_name in apps:
                if app_name.lower() in window_title_lower:
                    detected_role = role_key
                    match_found = True
                    break
            
            if match_found:
                break

        # Only emit signal if the ROLE actually changed
        if detected_role != self._last_role:
            print(f"🦎 Chameleon: Switched to [{detected_role.upper()}] (App: {window_title[:20]}...)")
            self._last_role = detected_role
            self.context_changed.emit(window_title, detected_role)

    def _get_active_window_title(self) -> str:
        """
        Platform-agnostic window title fetcher.
        Returns empty string on failure.
        """
        if not HAS_PYGETWINDOW:
            return ""

        try:
            window = gw.getActiveWindow()
            if window:
                return window.title.strip()
            return ""
        except Exception:
            # Active window might be None (e.g., desktop focused)
            return ""