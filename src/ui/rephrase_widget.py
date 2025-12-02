import uuid
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                             QPushButton, QLabel, QProgressBar, QDialog, QApplication)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent

from ..utils.config import config
from ..workers.generation_worker import GenerationRequest

class RephraseWidget(QDialog):
    """
    Floating widget for rewriting selected text.
    SOLID MODE: Large & Spacious.
    """
    
    text_ready = Signal(str)

    def __init__(self, assistant, parent=None):
        super().__init__(parent)
        self.assistant = assistant
        
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool
        )
        
        # 🚨 UPDATED SIZE
        self.resize(700, 600)
        
        self.current_request_id = None
        self.original_text = ""
        self.old_pos = None
        
        self._init_ui()
        self._apply_styles()
        
        if self.assistant:
            self.assistant.generation_worker.generation_completed.connect(self._on_success)
            self.assistant.generation_worker.generation_failed.connect(self._on_failure)

    def _init_ui(self):
        self.setObjectName("RephraseContainer")
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(25, 25, 25, 25)
        self.layout.setSpacing(15)

        # --- Header ---
        header = QHBoxLayout()
        title = QLabel("🔄 Rephrase")
        title.setObjectName("Title")
        
        btn_close = QPushButton("×")
        btn_close.setFixedSize(30, 30)
        btn_close.setObjectName("CloseButton")
        btn_close.clicked.connect(self.hide)
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(btn_close)
        self.layout.addLayout(header)

        # --- Original Text ---
        self.layout.addWidget(QLabel("Original Text:"))
        self.txt_original = QTextEdit()
        self.txt_original.setMaximumHeight(100)
        self.layout.addWidget(self.txt_original)

        # --- Instructions ---
        self.layout.addWidget(QLabel("Instructions (Optional):"))
        self.txt_instructions = QTextEdit()
        self.txt_instructions.setPlaceholderText("e.g., 'Make it more professional', 'Fix grammar'...")
        self.txt_instructions.setMaximumHeight(80)
        self.layout.addWidget(self.txt_instructions)

        # --- Progress ---
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 0)
        self.progress.hide()
        self.layout.addWidget(self.progress)

        # --- Result ---
        self.lbl_result = QLabel("Result:")
        self.lbl_result.hide()
        self.txt_result = QTextEdit()
        self.txt_result.hide()
        self.layout.addWidget(self.lbl_result)
        self.layout.addWidget(self.txt_result)

        # --- Buttons ---
        btn_layout = QHBoxLayout()
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.hide)
        self.btn_cancel.setObjectName("SecondaryButton")
        
        self.btn_action = QPushButton("Rephrase")
        self.btn_action.clicked.connect(self._handle_action)
        self.btn_action.setObjectName("PrimaryButton")
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_action)
        self.layout.addLayout(btn_layout)

    def _apply_styles(self):
        from .styles import styles
        self.setStyleSheet(styles.floating_widget + """
            QDialog#RephraseContainer {
                background-color: #21252b; 
                border: 2px solid #4a9eff;
            }
        """)

    def set_text(self, text: str):
        self.original_text = text
        self.txt_original.setText(text)
        self.txt_instructions.clear()
        self.txt_instructions.setFocus()
        self._reset_view()

    def _handle_action(self):
        if self.btn_action.text() == "Rephrase":
            self._start_rephrasing()
        else:
            self._copy_and_close()

    def _start_rephrasing(self):
        self.original_text = self.txt_original.toPlainText()
        if not self.original_text:
            return
        
        instructions = self.txt_instructions.toPlainText().strip()
        if not instructions:
            instructions = "Improve clarity and tone."

        self.btn_action.setEnabled(False)
        self.btn_action.setText("Processing...")
        self.progress.show()
        
        full_prompt = (
            f"Original Text:\n{self.original_text}\n\n"
            f"Instructions: {instructions}\n\n"
            f"Rephrased Text:"
        )

        self.current_request_id = str(uuid.uuid4())
        request = GenerationRequest(
            priority=1,
            request_id=self.current_request_id,
            prompt=full_prompt,
            system_prompt="You are a professional editor.",
            generation_type="writing"
        )
        
        self.assistant.generation_worker.add_request(request)

    def _on_success(self, req_id: str, result: str):
        if req_id != self.current_request_id: return
        
        self.progress.hide()
        self.lbl_result.show()
        self.txt_result.setText(result.strip())
        self.txt_result.show()
        
        self.btn_action.setText("Copy")
        self.btn_action.setEnabled(True)
        self.txt_result.setFocus()

    def _on_failure(self, req_id: str, error: str):
        if req_id != self.current_request_id: return
        
        self.progress.hide()
        self.btn_action.setText("Rephrase")
        self.btn_action.setEnabled(True)
        self.txt_instructions.setPlaceholderText(f"Error: {error}")

    def _copy_and_close(self):
        text = self.txt_result.toPlainText()
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        self.text_ready.emit(text)
        self.hide()
        
        # Resume monitoring
        if self.assistant:
            self.assistant.resume_monitoring()

    def _reset_view(self):
        self.txt_result.hide()
        self.lbl_result.hide()
        self.progress.hide()
        self.btn_action.setText("Rephrase")
        self.btn_action.setEnabled(True)

    # Dragging
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPosition().toPoint()
    def mouseMoveEvent(self, event: QMouseEvent):
        if self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()
    def mouseReleaseEvent(self, event: QMouseEvent):
        self.old_pos = None

    # 🚨 CRITICAL: Pause/Resume
    def showEvent(self, event):
        if self.assistant:
            self.assistant.pause_monitoring()
        super().showEvent(event)
        
    def closeEvent(self, event):
        if self.assistant:
            self.assistant.resume_monitoring()
        super().closeEvent(event)