"""
InkSage Core Services
=====================

This package contains the essential backend logic for the application,
including the AI engine, input monitoring, context awareness, and
state management.

Exposes the main classes for easier access via:
    from src.core import WritingAssistant, Engine, ...
"""

from .assistant import WritingAssistant
from .engine import Engine
from .text_buffer import TextBuffer
from .keyboard_monitor import KeyboardMonitor
from .context_sniffer import ContextSniffer

# Define the public API of this package
__all__ = [
    "WritingAssistant",
    "Engine",
    "TextBuffer",
    "KeyboardMonitor",
    "ContextSniffer",
]