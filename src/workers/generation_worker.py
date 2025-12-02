"""
InkSage Generation Worker
=========================

Handles asynchronous AI text generation in a dedicated background thread.
Uses a Priority Queue to ensure urgent requests (like manual completions)
are processed before background tasks.
"""

import time
import queue
import traceback
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from PySide6.QtCore import QThread, Signal, QMutex, QWaitCondition

@dataclass(order=True)
class GenerationRequest:
    """
    Represents a text generation request packet.
    'priority' determines processing order (Lower number = Higher Priority).
    """
    priority: int
    # field(compare=False) ensures we only sort by priority/timestamp
    request_id: str = field(compare=False)
    prompt: str = field(compare=False)
    system_prompt: str = field(compare=False, default=None)
    generation_type: str = field(compare=False, default="completion")
    parameters: Dict[str, Any] = field(compare=False, default_factory=dict)
    timestamp: float = field(compare=False, default_factory=time.time)


class GenerationWorker(QThread):
    """
    Background worker for handling text generation requests.
    Processes requests asynchronously to keep UI responsive.
    """
    
    # Signals
    generation_completed = Signal(str, str)  # request_id, result
    generation_failed = Signal(str, str)     # request_id, error
    generation_started = Signal(str)         # request_id
    queue_status_changed = Signal(int)       # queue_size
    
    def __init__(self, max_queue_size: int = 10):
        super().__init__()
        
        self.max_queue_size = max_queue_size
        self.request_queue = queue.PriorityQueue(maxsize=max_queue_size)
        
        # Thread synchronization
        self.mutex = QMutex()
        self.condition = QWaitCondition()
        self.running = False
        self.current_request: Optional[GenerationRequest] = None
        
        # The Engine instance (Lazy loaded in run)
        self.engine = None
        
        # Statistics
        self.processed_requests = 0
        self.failed_requests = 0
        self.total_processing_time = 0.0
        self.active_requests = set()

    def run(self) -> None:
        """Main worker thread loop."""
        print("⚙️ Worker: Thread started. Initializing Engine...")
        
        # 🚨 CIRCULAR IMPORT FIX: Import Engine here, not at the top
        try:
            from ..core.engine import Engine
            self.engine = Engine()
            if not self.engine.is_available():
                print("❌ Worker: Engine failed to initialize.")
                return
        except Exception as e:
            print(f"❌ Worker Critical: {e}")
            traceback.print_exc()
            return

        self.running = True
        
        while self.running:
            try:
                # 2. Wait for requests (Non-blocking check + WaitCondition)
                self.mutex.lock()
                if self.request_queue.empty():
                    self.condition.wait(self.mutex)
                self.mutex.unlock()

                if not self.running:
                    break

                # 3. Fetch Request
                try:
                    # Get the highest priority item
                    request = self.request_queue.get(block=False)
                except queue.Empty:
                    continue

                self.current_request = request
                self.active_requests.add(request.request_id)
                self.generation_started.emit(request.request_id)
                
                # 4. Process
                start_time = time.time()
                success = self._process_request(request)
                processing_time = time.time() - start_time
                
                # 5. Stats & Cleanup
                self.total_processing_time += processing_time
                if success:
                    self.processed_requests += 1
                else:
                    self.failed_requests += 1
                
                self.active_requests.discard(request.request_id)
                self.current_request = None
                self.queue_status_changed.emit(self.request_queue.qsize())
                
            except Exception as e:
                print(f"🔥 Worker Loop Error: {e}")
                traceback.print_exc()
        
        # Cleanup
        if self.engine:
            self.engine.cleanup()
        print("⚙️ Worker: Shutdown.")

    def _process_request(self, request: GenerationRequest) -> bool:
        """
        Routes the request to the Engine.
        """
        if not self.engine:
            self.generation_failed.emit(request.request_id, "Engine not initialized")
            return False

        try:
            # Map request params to Engine.generate() args
            kwargs = request.parameters.copy()
            
            # Adjust max_tokens based on type
            if request.generation_type == "completion":
                kwargs.setdefault('max_tokens', 64)
            else:
                kwargs.setdefault('max_tokens', 512)

            result = self.engine.generate(
                prompt=request.prompt,
                system_prompt=request.system_prompt,
                **kwargs
            )

            if result:
                self.generation_completed.emit(request.request_id, result)
                return True
            else:
                self.generation_failed.emit(request.request_id, "No text generated")
                return False

        except Exception as e:
            self.generation_failed.emit(request.request_id, str(e))
            return False

    def add_request(self, request: GenerationRequest) -> bool:
        """
        Thread-safe method to add a request.
        Handles Priority Queue logic (dropping low priority if full).
        """
        try:
            # Check if full
            if self.request_queue.full():
                self._remove_low_priority_request()

            # Add to queue
            self.request_queue.put(request, block=False)
            
            # Wake up thread
            self.mutex.lock()
            self.condition.wakeOne()
            self.mutex.unlock()
            
            self.queue_status_changed.emit(self.request_queue.qsize())
            return True

        except Exception as e:
            print(f"Error adding request: {e}")
            return False

    def _remove_low_priority_request(self):
        """
        Drops the lowest priority item to make room for high priority.
        """
        temp_items = []
        while not self.request_queue.empty():
            try:
                temp_items.append(self.request_queue.get(block=False))
            except queue.Empty:
                break
        
        # Sort: Priority (asc), Timestamp (asc)
        # We want to drop the Highest Number (Lowest Priority) and Oldest
        temp_items.sort(key=lambda x: (x.priority, x.timestamp))
        
        if temp_items:
            dropped = temp_items.pop() # Removes the last element (lowest priority)
            print(f"⚠️ Queue full. Dropped low-priority request: {dropped.request_id}")
            
        # Refill
        for item in temp_items:
            self.request_queue.put(item)

    def cancel_request(self, request_id: str) -> bool:
        """Removes a pending request from the queue."""
        self.mutex.lock()
        temp_items = []
        found = False
        
        # Drain queue
        while not self.request_queue.empty():
            try:
                item = self.request_queue.get(block=False)
                if item.request_id == request_id:
                    found = True
                else:
                    temp_items.append(item)
            except queue.Empty:
                break
        
        # Refill
        for item in temp_items:
            self.request_queue.put(item)
            
        self.mutex.unlock()
        if found:
            self.queue_status_changed.emit(self.request_queue.qsize())
        return found

    def stop(self):
        """Stop the worker thread safely."""
        self.running = False
        self.mutex.lock()
        self.condition.wakeOne()
        self.mutex.unlock()
        self.wait()