"""
InkSage Main Command Bar - PERSISTENT MODE
"""

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QApplication)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QCursor

from ..core.assistant import WritingAssistant, GenerationRequest
from ..utils.config import config
from .auto_write_dialog import AutoWriteDialog
from .rephrase_widget import RephraseWidget
from .suggestion_widget import SuggestionWidget
import uuid

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.assistant = WritingAssistant()
        self._setup_window_properties()
        self._init_ui()
        self._apply_styles()
        
        self.auto_write_dialog = None
        self.rephrase_dialog = None
        self.suggestion_widget = None

        self.assistant.status_changed.connect(self.update_status)
        self.assistant.suggestion_ready.connect(self.show_suggestion_popup)
        self.old_pos = None

    def _setup_window_properties(self):
        self.setWindowFlags(Qt.FramelessWindowHint)
        w = config.get('ui.window_size.width', 800)
        h = config.get('ui.window_size.height', 600)
        self.resize(w, h)
        self._center_on_screen()

    def _init_ui(self):
        self.central_widget = QWidget()
        self.central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(self.central_widget)
        
        layout = QVBoxLayout(self.central_widget)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        header = QHBoxLayout()
        self.lbl_title = QLabel("InkSage")
        self.lbl_title.setObjectName("Title")
        self.lbl_status = QLabel("Ready")
        self.lbl_status.setObjectName("Status")
        self.lbl_status.setAlignment(Qt.AlignRight)
        btn_close = QPushButton("×")
        btn_close.setFixedSize(30, 30)
        btn_close.setObjectName("CloseButton")
        btn_close.clicked.connect(self.hide) 
        
        header.addWidget(self.lbl_title)
        header.addStretch()
        header.addWidget(self.lbl_status)
        header.addWidget(btn_close)
        layout.addLayout(header)

        self.btn_auto_write = QPushButton("✨  Auto Write")
        self.btn_auto_write.setObjectName("BigButton")
        self.btn_auto_write.setMinimumHeight(60)
        self.btn_auto_write.clicked.connect(self.open_auto_write)
        layout.addWidget(self.btn_auto_write)

        features_layout = QHBoxLayout()
        features_layout.setSpacing(15)
        btn_rephrase = QPushButton("🔄 Rephrase")
        btn_rephrase.setObjectName("FeatureButton")
        btn_rephrase.setMinimumHeight(50)
        btn_rephrase.clicked.connect(self.open_rephrase)
        btn_complete = QPushButton("⚡ Quick Complete")
        btn_complete.setObjectName("FeatureButton")
        btn_complete.setMinimumHeight(50)
        btn_complete.clicked.connect(self.trigger_quick_complete)
        
        features_layout.addWidget(btn_rephrase)
        features_layout.addWidget(btn_complete)
        layout.addLayout(features_layout)
        layout.addStretch()

    def _apply_styles(self):
        from .styles import styles
        self.setStyleSheet(styles.main_window)

    @Slot(str)
    def update_status(self, text):
        self.lbl_status.setText(text)

    @Slot(str)
    def show_suggestion_popup(self, text):
        if not self.suggestion_widget:
            self.suggestion_widget = SuggestionWidget(parent=None)
        
        self.suggestion_widget.set_suggestions([text])
        self.suggestion_widget.show_at_cursor()
        
        # 🚨 CHANGE: Removed 'self.hide()' so main window stays open
        # if self.isVisible(): self.hide() <--- DELETED

    def trigger_quick_complete(self):
        self.lbl_status.setText("Checking buffer...")
        context = self.assistant.text_buffer.get_context()
        
        if context and context.strip():
            self.lbl_status.setText("Thinking...")
            self.assistant.trigger_manual_completion()
        else:
            self.lbl_status.setText("Running Test...")
            req_id = str(uuid.uuid4())
            request = GenerationRequest(
                priority=1,
                request_id=req_id,
                prompt="The quick brown fox jumps over the", 
                system_prompt="You are a sentence completer.",
                generation_type="completion"
            )
            self.assistant.active_requests[req_id] = "completion" # Logic fix for dict tracking
            self.assistant.generation_worker.add_request(request)

    def open_auto_write(self):
        if not self.auto_write_dialog:
            self.auto_write_dialog = AutoWriteDialog(self.assistant, parent=self)
        self._center_dialog(self.auto_write_dialog)
        self.auto_write_dialog.show()

    def open_rephrase(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if not self.rephrase_dialog:
            self.rephrase_dialog = RephraseWidget(self.assistant, parent=self)
        self.rephrase_dialog.set_text(text)
        self._center_dialog(self.rephrase_dialog)
        self.rephrase_dialog.show()

    def _center_dialog(self, dialog):
        geo = self.geometry()
        center = geo.center()
        dialog.move(
            center.x() - dialog.width() // 2,
            center.y() - dialog.height() // 2
        )

    def _center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )

    def show_at_cursor(self):
        pos = QCursor.pos()
        self.move(pos.x(), pos.y())
        self.show()
        self.raise_()
        self.activateWindow()

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

    def closeEvent(self, event):
        if self.assistant:
            self.assistant.cleanup()
        event.accept()