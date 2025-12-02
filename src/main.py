"""
InkSage - AI Context Engine
===========================

Main Entry Point.
Initializes the GUI, System Tray, and Background Monitors.
"""

import sys
import signal
import logging
from pathlib import Path

# Add project root to python path to ensure imports work
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QSystemTrayIcon
from PySide6.QtGui import QIcon

# Import InkSage Components
from src.ui.main_window import MainWindow
from src.ui.tray_icon import InkSageTray
from src.core.keyboard_monitor import KeyboardMonitor
from src.utils.config import config

class InkSageApp:
    def __init__(self):
        self._setup_logging()
        self.app = self._init_qt_app()
        
        # Core Components
        self.main_window = None
        self.tray = None
        self.keyboard_monitor = None

    def _setup_logging(self):
        """Configure logging format."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        self.logger = logging.getLogger("InkSage")

    def _init_qt_app(self):
        """Initialize the PySide6 Application."""
        app = QApplication(sys.argv)
        app.setApplicationName(config.get('app.name', 'InkSage'))
        app.setApplicationVersion(config.get('app.version', '1.0.0'))
        
        # Critical: Don't exit when the main window is hidden (System Tray mode)
        app.setQuitOnLastWindowClosed(False)
        return app

    def start(self):
        """Boot up the system."""
        self.logger.info("🚀 InkSage starting up...")

        try:
            # 1. Initialize Main Window (The Command Bar)
            # This implicitly initializes the 'Assistant' and 'Engine'
            self.main_window = MainWindow()
            
            # 2. Initialize System Tray (The Background Presence)
            self.tray = InkSageTray()
            self._connect_tray_signals()

            # 3. Initialize Global Inputs (The Eyes)
            # We pass the text buffer from the assistant to the monitor
            if self.main_window.assistant:
                self.keyboard_monitor = KeyboardMonitor(self.main_window.assistant.text_buffer)
                self._connect_input_signals()
                
                # Start Monitoring
                if self.keyboard_monitor.start():
                    self.logger.info("✅ Keyboard Monitor Active")
                else:
                    self.logger.warning("⚠️ Keyboard Monitor failed to start (Check permissions)")

            # 4. Startup Notification
            self.tray.showMessage(
                "InkSage Ready",
                "Press Ctrl+Shift+Q to open.",
                QSystemTrayIcon.Information,
                3000
            )

            # 5. Show Window Immediately (Better UX)
            self.main_window.show()
            self.main_window.activateWindow()

            # 6. Run Event Loop
            # Allow Ctrl+C to kill the app in terminal for debugging
            signal.signal(signal.SIGINT, signal.SIG_DFL)
            return self.app.exec()

        except Exception as e:
            self.logger.critical(f"🔥 Fatal Error during startup: {e}", exc_info=True)
            return 1

    def _connect_tray_signals(self):
        """Link Tray actions to App logic."""
        self.tray.show_requested.connect(self.main_window.show_at_cursor)
        self.tray.quit_requested.connect(self._quit)

    def _connect_input_signals(self):
        """Link Global Hotkeys to App logic."""
        self.keyboard_monitor.hotkey_triggered.connect(self._handle_hotkey)

    def _handle_hotkey(self, action: str):
        """Route global hotkeys to specific functions."""
        self.logger.debug(f"Hotkey triggered: {action}")
        
        if action == "toggle_assistant":
            if self.main_window.isVisible():
                self.main_window.hide()
            else:
                self.main_window.show_at_cursor()
                
        elif action == "quick_complete":
            self.main_window.trigger_quick_complete()
            
        elif action == "rephrase":
            # If main window is hidden, show it first
            if not self.main_window.isVisible():
                self.main_window.show_at_cursor()
            # Then trigger rephrase dialog
            self.main_window.open_rephrase()

    def _quit(self):
        """Clean shutdown."""
        self.logger.info("Shutting down...")
        
        if self.keyboard_monitor:
            self.keyboard_monitor.stop()
            
        if self.main_window:
            self.main_window.close() # Triggers assistant cleanup
            
        if self.tray:
            self.tray.hide()
            
        self.app.quit()

def main():
    app = InkSageApp()
    sys.exit(app.start())

if __name__ == "__main__":
    main()