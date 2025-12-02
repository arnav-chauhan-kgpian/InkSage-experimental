"""
InkSage Text Buffer
===================

A thread-safe rolling buffer that manages the short-term memory
of the user's typing session. It captures keystrokes and maintains
a sliding window of text to provide context for the AI.
"""

import time
from threading import Lock, Timer
from typing import Optional, Callable, Dict

from ..utils.config import config

class TextBuffer:
    """
    A thread-safe circular-like buffer for string data.
    It synchronizes what the user sees on screen with what the AI sees in RAM.
    """
    
    def __init__(self, on_context_ready: Optional[Callable[[str], None]] = None):
        # Config
        self.max_size = config.get('text.buffer_size', 2000)
        self.debounce_delay = config.get('text.debounce_delay', 500) / 1000.0
        self.min_context_length = config.get('text.min_context_length', 10)
        
        # State
        self.buffer = ""
        self.lock = Lock()
        self.last_update_time = 0
        
        # Debouncing
        self.on_context_ready = on_context_ready
        self.debounce_timer: Optional[Timer] = None
        
        # Stats
        self.session_chars = 0
        
    def append(self, text: str) -> None:
        """Add character(s) to the buffer."""
        with self.lock:
            self.buffer += text
            self.session_chars += len(text)
            self.last_update_time = time.time()
            
            # Enforce Hard Limit (Rolling Window)
            if len(self.buffer) > self.max_size:
                # Keep the last N characters
                self.buffer = self.buffer[-self.max_size:]

            self._reset_debounce()

    def handle_backspace(self) -> None:
        """Remove the last character (Critical for sync)."""
        with self.lock:
            if self.buffer:
                self.buffer = self.buffer[:-1]
                self.last_update_time = time.time()
                self._reset_debounce()

    def clear(self) -> None:
        """Wipe memory (e.g., when changing active windows)."""
        with self.lock:
            self.buffer = ""
            self._cancel_timer()

    def get_context(self) -> str:
        """
        Snapshot the current buffer for the AI.
        
        Returns:
            The raw string context (e.g., the last 2000 chars).
        """
        with self.lock:
            return self.buffer.strip()

    # =========================================================================
    # ⏱️ Debounce Logic
    # =========================================================================

    def _reset_debounce(self):
        """Resets the timer that triggers the AI."""
        self._cancel_timer()
        
        # Only start timer if we have enough context
        if len(self.buffer) >= self.min_context_length:
            self.debounce_timer = Timer(self.debounce_delay, self._fire_trigger)
            self.debounce_timer.start()

    def _fire_trigger(self):
        """Called when user stops typing for {debounce_delay} seconds."""
        if self.on_context_ready:
            context = self.get_context()
            if context:
                self.on_context_ready(context)

    def _cancel_timer(self):
        if self.debounce_timer:
            self.debounce_timer.cancel()
            self.debounce_timer = None

    # =========================================================================
    # 📊 Analytics
    # =========================================================================

    def get_stats(self) -> Dict[str, int]:
        with self.lock:
            return {
                'current_length': len(self.buffer),
                'total_chars_typed': self.session_chars
            }

    def cleanup(self):
        """Stop any pending timers."""
        self._cancel_timer()