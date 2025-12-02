"""
InkSage Utilities
=================

General-purpose helper modules used across the application.
"""

from .config import config
from .clipboard import ClipboardManager, clipboard_manager

__all__ = [
    "config",
    "ClipboardManager",
    "clipboard_manager",
]