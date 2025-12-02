"""
InkSage Assistant Core - LOGIC FIXED
"""

import uuid
import time
from PySide6.QtCore import QObject, Signal

from .context_sniffer import ContextSniffer
from .text_buffer import TextBuffer
from .keyboard_monitor import KeyboardMonitor
from ..workers.generation_worker import GenerationWorker, GenerationRequest
from ..utils.config import config

class WritingAssistant(QObject):
    
    suggestion_ready = Signal(str)
    status_changed = Signal(str)
    error_occurred = Signal(str)
    generation_started = Signal()
    generation_completed = Signal()
    
    def __init__(self):
        super().__init__()
        
        self.enabled = True
        self.auto_completion_enabled = config.get('keyboard.enabled', True)
        self.is_paused = False
        self.last_suggestion_time = 0
        self.suggestion_cooldown = config.get('text.debounce_delay', 500) / 1000.0
        
        # 🚨 DICTIONARY TO TRACK REQUEST TYPES
        self.active_requests = {} 
        self.current_app_context = "general"

        self._update_status("Initializing...")
        self.context_sniffer = ContextSniffer()
        self.context_sniffer.context_changed.connect(self._handle_context_change)
        self.context_sniffer.start()
        self.text_buffer = TextBuffer(on_context_ready=self._handle_buffer_ready)
        self.keyboard_monitor = KeyboardMonitor(self.text_buffer)
        self.keyboard_monitor.text_captured.connect(self._handle_manual_trigger)
        self.keyboard_monitor.hotkey_triggered.connect(self._handle_hotkey)
        self._init_generation_worker()
        if self.auto_completion_enabled:
            self._start_monitoring()
        self._update_status("Ready")

    def _init_generation_worker(self) -> None:
        max_queue = config.get('performance.max_concurrent_requests', 2)
        self.generation_worker = GenerationWorker(max_queue_size=max_queue)
        self.generation_worker.generation_completed.connect(self._handle_generation_completed)
        self.generation_worker.generation_failed.connect(self._handle_generation_failed)
        self.generation_worker.generation_started.connect(self._handle_generation_started)
        self.generation_worker.start()

    def pause_monitoring(self):
        self.is_paused = True
        if self.keyboard_monitor: self.keyboard_monitor.pause()
        if self.text_buffer: self.text_buffer.clear()
        self._update_status("Paused")

    def resume_monitoring(self):
        self.is_paused = False
        if self.enabled and self.auto_completion_enabled and self.keyboard_monitor:
            self.keyboard_monitor.resume()
            self._update_status("Monitoring")

    def _start_monitoring(self) -> bool:
        if self.keyboard_monitor.start():
            self._update_status(f"Monitoring ({self.current_app_context})")
            return True
        return False

    def _stop_monitoring(self) -> None:
        self.keyboard_monitor.stop()
        self._update_status("Paused")

    def _handle_context_change(self, new_app_name: str, detected_role: str):
        if self.current_app_context != detected_role:
            self.current_app_context = detected_role
            self._update_status(f"Role: {detected_role.upper()}")

    def _handle_buffer_ready(self, text_context: str) -> None:
        if self.is_paused or not self.enabled or not text_context.strip(): return
        if (time.time() - self.last_suggestion_time) < self.suggestion_cooldown: return
        self.last_suggestion_time = time.time()
        self._request_generation(text_context, trigger_type="auto")

    def _handle_manual_trigger(self, text: str) -> None:
        if self.is_paused: return
        if self.enabled and text.strip():
            self._request_generation(text, trigger_type="manual")

    def _handle_hotkey(self, action: str) -> None:
        if action == "toggle_assistant": self.toggle_enabled()
        elif action == "quick_complete": self.trigger_manual_completion()
        elif action == "dictate": self._handle_dictation()

    def _request_generation(self, text_context: str, trigger_type: str = "auto") -> None:
        system_prompt = config.get_role_prompt(self.current_app_context)
        req_id = str(uuid.uuid4())
        
        request = GenerationRequest(
            request_id=req_id,
            prompt=text_context,
            system_prompt=system_prompt, 
            generation_type="completion", # 🚨 TAGGED AS COMPLETION
            priority=1 if trigger_type == "manual" else 2
        )

        if self.generation_worker.add_request(request):
            self.active_requests[req_id] = "completion"
            self._update_status("Thinking...")

    def _handle_dictation(self):
        self._update_status("🎤 Listening...")

    def _handle_generation_started(self, request_id: str):
        if request_id in self.active_requests:
            self.generation_started.emit()

    def _handle_generation_completed(self, request_id: str, result: str):
        # Check if we are tracking this request
        if request_id in self.active_requests:
            req_type = self.active_requests.pop(request_id)
            clean_result = result.strip()
            
            # 🚨 CRITICAL FIX: Only show popup if type was 'completion'
            if req_type == "completion":
                if clean_result:
                    self.suggestion_ready.emit(clean_result)
                    self._update_status("Ready")
                else:
                    self._update_status("No suggestion")
            
            # If type was "writing" or "rephrase", we ignore it here.
            # The Dialogs catch those signals directly.
            
            self.generation_completed.emit()

    def _handle_generation_failed(self, request_id: str, error: str):
        if request_id in self.active_requests:
            self.active_requests.pop(request_id)
            self._update_status("Error")
            print(f"Generation Error: {error}") 

    def toggle_enabled(self):
        self.enabled = not self.enabled
        status = "Enabled" if self.enabled else "Disabled"
        self._update_status(f"Assistant {status}")
        if self.enabled and self.auto_completion_enabled: self._start_monitoring()
        else: self._stop_monitoring()

    def trigger_manual_completion(self):
        context = self.text_buffer.get_context()
        if context: self._request_generation(context, trigger_type="manual")

    def _update_status(self, msg: str):
        self.current_status = msg
        self.status_changed.emit(msg)

    def cleanup(self):
        if self.context_sniffer: self.context_sniffer.stop()
        if self.keyboard_monitor: self.keyboard_monitor.stop()
        if self.generation_worker:
            self.generation_worker.stop()
            self.generation_worker.wait()
        if self.text_buffer: self.text_buffer.cleanup()