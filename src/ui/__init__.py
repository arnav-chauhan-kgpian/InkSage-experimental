"""
InkSage UI Package
==================

Contains all visual components of the application, including:
- The Main Command Bar (MainWindow)
- The System Tray Icon (InkSageTray)
- Floating Dialogs (AutoWrite, Rephrase, Suggestions)
- Styling Logic (StyleManager)
"""

from .styles import styles
from .suggestion_widget import SuggestionWidget
from .auto_write_dialog import AutoWriteDialog
from .rephrase_widget import RephraseWidget
from .main_window import MainWindow
from .tray_icon import InkSageTray

__all__ = [
    "MainWindow",
    "InkSageTray",
    "AutoWriteDialog",
    "RephraseWidget",
    "SuggestionWidget",
    "styles",
]