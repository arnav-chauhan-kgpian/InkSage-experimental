import uuid
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, 
                             QPushButton, QLabel, QProgressBar, QApplication)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication, QCursor

from ..utils.config import config
from ..workers.generation_worker import GenerationRequest

class AutoWriteDialog(QDialog):
    """
    Floating dialog for generating new content.
    SOLID MODE: Large & Spacious.
    """
    
    text_accepted = Signal(str)

    def __init__(self, assistant, parent=None):
        super().__init__(parent)
        self.assistant = assistant
        
        # 1. Window Setup
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.resize(700, 600)
        
        self.current_request_id = None
        self.is_generating = False
        self.old_pos = None
        
        # 2. Setup UI
        self._init_ui()
        self._apply_styles()
        
        # 3. Connect Signals
        if self.assistant:
            self.assistant.generation_worker.generation_completed.connect(self._on_generation_success)
            self.assistant.generation_worker.generation_failed.connect(self._on_generation_failed)

    def _init_ui(self):
        self.setObjectName("AutoWriteContainer")
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(25, 25, 25, 25)
        self.layout.setSpacing(15)

        # --- Header ---
        header = QHBoxLayout()
        title = QLabel("✨ Auto Write")
        title.setObjectName("Title")
        
        btn_close = QPushButton("×")
        btn_close.setFixedSize(30, 30)
        btn_close.clicked.connect(self.hide_and_reset)
        btn_close.setObjectName("CloseButton")
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(btn_close)
        self.layout.addLayout(header)

        # --- Prompt Input ---
        self.lbl_instruction = QLabel("Describe what you want to write:")
        self.input_prompt = QTextEdit()
        self.input_prompt.setPlaceholderText("e.g., 'Write a professional email about project delays...'")
        self.input_prompt.setMaximumHeight(120) 
        self.layout.addWidget(self.lbl_instruction)
        self.layout.addWidget(self.input_prompt)

        # --- Progress Bar ---
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 0)
        self.progress.hide()
        self.layout.addWidget(self.progress)

        # --- Result Preview ---
        self.lbl_result = QLabel("Preview:")
        self.lbl_result.hide()
        
        self.preview_area = QTextEdit()
        self.preview_area.setPlaceholderText("Generated text will appear here...")
        self.preview_area.hide()
        self.layout.addWidget(self.lbl_result)
        self.layout.addWidget(self.preview_area)

        # --- Action Buttons ---
        btn_layout = QHBoxLayout()
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.hide_and_reset)
        self.btn_cancel.setObjectName("SecondaryButton")
        
        self.btn_reset = QPushButton("Try Again")
        self.btn_reset.clicked.connect(self.reset_for_new)
        self.btn_reset.hide()
        self.btn_reset.setObjectName("SecondaryButton")
        
        self.btn_action = QPushButton("Generate")
        self.btn_action.clicked.connect(self._handle_action_click)
        self.btn_action.setObjectName("PrimaryButton")
        
        btn_layout.addWidget(self.btn_reset)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_action)
        self.layout.addLayout(btn_layout)

    def _apply_styles(self):
        from .styles import styles
        self.setStyleSheet(styles.floating_widget + """
            QDialog#AutoWriteContainer {
                background-color: #21252b; 
                border: 2px solid #4a9eff;
            }
        """)

    # ==========================================
    # Logic
    # ==========================================

    def _handle_action_click(self):
        if self.btn_action.text() == "Generate":
            self._start_generation()
        else:
            self._finalize_result()

    def _start_generation(self):
        prompt = self.input_prompt.toPlainText().strip()
        if not prompt: return

        # 🚨 PREVENT MULTIPLE CLICKS
        if self.is_generating: return

        self.is_generating = True
        
        # 🚨 CLEAR OLD DATA
        self.preview_area.clear()
        
        # UI Update
        self.input_prompt.setEnabled(False)
        self.btn_action.setEnabled(False)
        self.btn_action.setText("Thinking...")
        self.progress.show()
        self.btn_reset.hide()

        self.current_request_id = str(uuid.uuid4())
        
        system_role = "You are a helpful assistant."
        if hasattr(self.assistant, 'current_app_context'):
             system_role = config.get_role_prompt(self.assistant.current_app_context)
        
        request = GenerationRequest(
            priority=1,
            request_id=self.current_request_id,
            prompt=prompt,
            system_prompt=system_role,
            generation_type="writing"
        )
        self.assistant.generation_worker.add_request(request)

    def _on_generation_success(self, req_id, text):
        # Ignore old requests or cross-talk
        if req_id != self.current_request_id: return
        
        self.is_generating = False
        self.progress.hide()
        
        self.lbl_result.show()
        self.preview_area.setText(text)
        self.preview_area.show()
        
        # Shrink prompt area
        self.input_prompt.setMaximumHeight(60)
        self.preview_area.setFocus()
        
        self.btn_action.setText("Copy & Close")
        self.btn_action.setEnabled(True)
        self.btn_reset.show()

    def _on_generation_failed(self, req_id, error):
        if req_id != self.current_request_id: return
        
        self.is_generating = False
        self.progress.hide()
        self.input_prompt.setEnabled(True)
        self.btn_action.setEnabled(True)
        self.btn_action.setText("Generate")
        self.input_prompt.setPlaceholderText(f"Error: {error}")

    def reset_for_new(self):
        """Clear result area for a new attempt."""
        self.preview_area.clear()
        self.preview_area.hide()
        self.lbl_result.hide()
        
        self.input_prompt.setEnabled(True)
        self.input_prompt.setMaximumHeight(120)
        self.input_prompt.setFocus()
        
        self.btn_action.setText("Generate")
        self.btn_reset.hide()

    def _finalize_result(self):
        text = self.preview_area.toPlainText()
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        self.text_accepted.emit(text)
        self.hide_and_reset()

    def hide_and_reset(self):
        self.hide()
        self.current_request_id = None
        self.is_generating = False
        self.reset_for_new()
        self.input_prompt.clear()
        
        if self.assistant:
            self.assistant.resume_monitoring()

    # 🚨 BETTER POSITIONING LOGIC
    def showEvent(self, event):
        if self.assistant:
            self.assistant.pause_monitoring()
        
        # Center on the ACTIVE screen (where the mouse is)
        screen = QGuiApplication.screenAt(QCursor.pos())
        if not screen:
            screen = QGuiApplication.primaryScreen()
            
        geo = screen.geometry()
        x = geo.x() + (geo.width() - self.width()) // 2
        y = geo.y() + (geo.height() - self.height()) // 2
        self.move(x, y)
            
        super().showEvent(event)
        
    def closeEvent(self, event):
        if self.assistant:
            self.assistant.resume_monitoring()
        super().closeEvent(event)
    
    # Dragging
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPosition().toPoint()
    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()
    def mouseReleaseEvent(self, event):
        self.old_pos = None