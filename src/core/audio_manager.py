"""
InkSage Audio Manager
=====================

Handles microphone input and local speech-to-text transcription
using Faster-Whisper.
"""

import os
import tempfile
import threading
from typing import Optional
from PySide6.QtCore import QObject, Signal
from ..utils.config import config

# Optional Dependencies
try:
    import pyaudio
    import wave
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    print("⚠️ PyAudio not found. Voice features disabled.")

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("⚠️ faster-whisper not found. Voice features disabled.")


class AudioManager(QObject):
    """
    Manages audio recording and transcription in a background thread.
    """
    
    transcription_finished = Signal(str)
    recording_started = Signal()
    recording_stopped = Signal()
    error_occurred = Signal(str)

    def __init__(self):
        super().__init__()
        self.enabled = config.get('voice.enabled', False)
        
        # Audio Configuration
        self.chunk = 1024
        self.format = pyaudio.paInt16 if AUDIO_AVAILABLE else None
        self.channels = 1
        self.rate = 16000 # Whisper expects 16k sample rate
        
        self.is_recording = False
        self.frames = []
        self._thread: Optional[threading.Thread] = None
        self.model = None # Lazy loaded

    def start_recording(self):
        """Begin capturing audio from the microphone."""
        if not self.enabled:
            self.error_occurred.emit("Voice features are disabled in config.")
            return
            
        if not AUDIO_AVAILABLE or not WHISPER_AVAILABLE:
            self.error_occurred.emit("Missing audio libraries (PyAudio/Faster-Whisper).")
            return

        if self.is_recording:
            return

        self.is_recording = True
        self.frames = []
        
        # Start recording in a separate thread to keep UI responsive
        self._thread = threading.Thread(target=self._record_loop, daemon=True)
        self._thread.start()
        
        self.recording_started.emit()

    def stop_recording(self):
        """Stop capturing and trigger transcription."""
        if not self.is_recording:
            return

        self.is_recording = False
        # The loop in _record_loop will break, triggering _save_and_transcribe
        self.recording_stopped.emit()

    def _record_loop(self):
        """Background loop for reading audio stream."""
        try:
            p = pyaudio.PyAudio()
            stream = p.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )

            while self.is_recording:
                data = stream.read(self.chunk)
                self.frames.append(data)

            stream.stop_stream()
            stream.close()
            p.terminate()

            # Process the captured audio immediately
            self._save_and_transcribe()
            
        except Exception as e:
            self.error_occurred.emit(f"Microphone Error: {e}")
            self.is_recording = False

    def _save_and_transcribe(self):
        """Save WAV to temp disk and run Whisper inference."""
        if not self.frames:
            return

        temp_filename = ""
        try:
            # 1. Write frames to a temporary WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                temp_filename = temp_wav.name
                with wave.open(temp_filename, 'wb') as wf:
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(pyaudio.PyAudio().get_sample_size(self.format))
                    wf.setframerate(self.rate)
                    wf.writeframes(b''.join(self.frames))

            # 2. Run Inference
            if WHISPER_AVAILABLE:
                text = self._run_whisper(temp_filename)
                if text.strip():
                    self.transcription_finished.emit(text)
            
        except Exception as e:
            self.error_occurred.emit(f"Transcription Failed: {str(e)}")
            
        finally:
            # 3. Cleanup temp file
            if temp_filename and os.path.exists(temp_filename):
                try:
                    os.remove(temp_filename)
                except OSError:
                    pass

    def _run_whisper(self, audio_path: str) -> str:
        """Load model (if needed) and transcribe file."""
        if self.model is None:
            model_size = config.get('voice.model_size', 'base')
            device_type = config.get('voice.device', 'cpu') # 'auto', 'cuda', 'cpu'
            
            # Auto-select best device if 'auto'
            if device_type == 'auto':
                # Simple check: faster-whisper handles CUDA if installed
                device_type = 'cuda' # Let faster-whisper fallback if needed
            
            print(f"🎙️ Loading Whisper Model ({model_size}) on {device_type}...")
            
            # int8 quantization is faster on CPU
            compute_type = "int8" if device_type == "cpu" else "float16"
            
            self.model = WhisperModel(
                model_size, 
                device=device_type, 
                compute_type=compute_type
            )

        # Transcribe
        segments, _ = self.model.transcribe(audio_path, beam_size=5)
        
        # Combine all segments into one string
        full_text = " ".join([segment.text for segment in segments])
        return full_text.strip()