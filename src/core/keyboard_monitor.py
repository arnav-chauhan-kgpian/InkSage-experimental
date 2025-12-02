"""
InkSage Keyboard Monitor - FIXED
Correctly handles Left/Right modifiers (Ctrl, Shift, Alt).
"""

import time
import queue
from threading import Thread, Event
from typing import Optional, Set, Dict, Any
from PySide6.QtCore import QObject, Signal

from ..utils.config import config

# Check for pynput availability
try:
    from pynput import keyboard
    from pynput.keyboard import Key, KeyCode, Listener
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    print("⚠️ pynput not available. Keyboard features disabled.")


class KeyboardMonitor(QObject):
    """
    Background worker that listens for global keystrokes.
    """
    
    # Signals
    text_captured = Signal(str)    
    hotkey_triggered = Signal(str)
    
    def __init__(self, text_buffer=None):
        super().__init__()
        
        if not PYNPUT_AVAILABLE:
            return
        
        self.text_buffer = text_buffer
        self.running = False
        self.paused = False
        
        self.input_queue: queue.Queue = queue.Queue()
        self.listener: Optional[Listener] = None
        self.processor_thread: Optional[Thread] = None
        self.stop_event = Event()
        
        self.enabled = config.get('keyboard.enabled', True)
        self.trigger_keys = set(config.get('keyboard.trigger_keys', ['enter', 'tab']))
        self.hotkeys = config.get('keyboard.hotkeys', {})
        
        # State
        self.current_modifiers: Set[str] = set()
        self.last_key_time = 0.0
        
        self.hotkey_combinations = self._parse_hotkeys()

    def start(self) -> bool:
        if not PYNPUT_AVAILABLE or not self.enabled: return False
        if self.running: return True
        
        try:
            self.running = True
            self.stop_event.clear()
            
            self.processor_thread = Thread(target=self._process_queue, daemon=True)
            self.processor_thread.start()

            self.listener = Listener(on_press=self._on_press_producer, on_release=self._on_release_producer)
            self.listener.start()
            return True
        except Exception as e:
            print(f"Error starting keyboard monitor: {e}")
            self.running = False
            return False

    def stop(self) -> None:
        self.running = False
        self.stop_event.set()
        if self.listener:
            self.listener.stop()
            self.listener = None
        with self.input_queue.mutex:
            self.input_queue.queue.clear()

    def pause(self) -> None: self.paused = True
    def resume(self) -> None: self.paused = False

    # --- Producer ---
    def _on_press_producer(self, key):
        if self.running: self.input_queue.put(("press", key, time.time()))

    def _on_release_producer(self, key):
        if self.running: self.input_queue.put(("release", key, time.time()))

    # --- Consumer ---
    def _process_queue(self):
        while not self.stop_event.is_set():
            try:
                event_type, key, timestamp = self.input_queue.get(timeout=0.5)
                if event_type == "press": self._handle_press_logic(key, timestamp)
                elif event_type == "release": self._handle_release_logic(key)
                self.input_queue.task_done()
            except queue.Empty: continue
            except Exception as e: print(f"Keyboard Monitor Error: {e}")

    # --- Logic ---
    def _handle_press_logic(self, key, timestamp: float):
        self.last_key_time = timestamp

        # 1. Update Modifiers
        if self._is_modifier(key):
            self.current_modifiers.add(self._get_key_name(key))
        
        # 2. Check Hotkeys
        if self._check_hotkeys(key):
            return

        if self.paused: return

        # 3. Clear on Navigation
        if key in [Key.up, Key.down, Key.left, Key.right, Key.home, Key.end]:
             if self.text_buffer: self.text_buffer.clear()
             return

        # 4. Text Capture
        text = self._key_to_text(key)
        if text:
            if self.text_buffer: self.text_buffer.append(text)
            if self._should_trigger_completion(key) and self.text_buffer:
                context = self.text_buffer.get_context()
                if context: self.text_captured.emit(context)
        elif key == Key.backspace:
            if self.text_buffer: self.text_buffer.handle_backspace()

    def _handle_release_logic(self, key):
        key_name = self._get_key_name(key)
        if key_name in self.current_modifiers:
            self.current_modifiers.discard(key_name)

    # --- Helpers ---
    def _is_modifier(self, key) -> bool:
        return key in [Key.ctrl_l, Key.ctrl_r, Key.shift, Key.shift_r, Key.alt_l, Key.alt_r, Key.cmd]

    def _get_key_name(self, key) -> str:
        if isinstance(key, Key): return key.name
        return 'char'

    def _check_hotkeys(self, key) -> bool:
        """
        Checks if the current key press completes a hotkey combination.
        """
        for action, reqs in self.hotkey_combinations.items():
            required_groups = reqs['modifiers'] # List of sets (e.g. [{ctrl_l, ctrl_r}, {shift_l...}])
            trigger_key = reqs['key']

            # 1. Check Trigger Key
            key_match = False
            if isinstance(key, KeyCode) and hasattr(key, 'char'):
                 if key.char and trigger_key and key.char.lower() == trigger_key.lower():
                     key_match = True
            elif isinstance(key, Key):
                 if key.name == trigger_key:
                     key_match = True

            if not key_match:
                continue

            # 2. Check Modifiers (The Fix)
            # We verify that FOR EACH required group (like "Ctrl"), 
            # AT LEAST ONE key from that group is currently pressed.
            all_mods_met = True
            for group in required_groups:
                # Is any key from this group pressed?
                if not any(m in self.current_modifiers for m in group):
                    all_mods_met = False
                    break
            
            if all_mods_met:
                self.hotkey_triggered.emit(action)
                return True
        
        return False

    def _parse_hotkeys(self) -> Dict:
        """
        Parses config strings like 'ctrl+shift+c' into logic groups.
        Returns: {'quick_complete': {'modifiers': [{'ctrl_l', 'ctrl_r'}, {'shift', 'shift_r'}], 'key': 'c'}}
        """
        parsed = {}
        for action, hotkey_str in self.hotkeys.items():
            parts = [p.strip().lower() for p in hotkey_str.split('+')]
            modifier_groups = []
            trigger_key = None
            
            for part in parts:
                if part == 'ctrl':
                    modifier_groups.append({'ctrl_l', 'ctrl_r'})
                elif part == 'shift':
                    modifier_groups.append({'shift', 'shift_r'})
                elif part == 'alt':
                    modifier_groups.append({'alt_l', 'alt_r'})
                elif part == 'cmd':
                    modifier_groups.append({'cmd'})
                elif part in ['ctrl_l', 'ctrl_r', 'shift_l', 'shift_r', 'alt_l', 'alt_r']:
                    # Specific modifier requested
                    modifier_groups.append({part})
                else:
                    trigger_key = part
            
            if trigger_key:
                parsed[action] = {'modifiers': modifier_groups, 'key': trigger_key}
        
        return parsed

    def _key_to_text(self, key) -> str:
        if hasattr(key, 'char') and key.char: return key.char
        if key == Key.space: return ' '
        if key == Key.enter: return '\n'
        if key == Key.tab: return '\t'
        return ''

    def _should_trigger_completion(self, key) -> bool:
        if key == Key.space and 'space' in self.trigger_keys: return True
        if key == Key.enter and 'enter' in self.trigger_keys: return True
        if key == Key.tab and 'tab' in self.trigger_keys: return True
        return False