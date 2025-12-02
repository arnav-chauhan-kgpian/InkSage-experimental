"""
InkSage Suggestion Overlay
==========================
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QListWidgetItem, 
                             QApplication)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent, QCursor, QGuiApplication

from ..utils.config import config
from ..utils.clipboard import clipboard_manager # Use the global instance

class SuggestionWidget(QWidget):
    suggestion_selected = Signal(str)
    widget_closed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 1. Window Configuration
        self.setWindowFlags(
            Qt.ToolTip | 
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint
        )
        
        self.suggestions = []
        self._init_ui()
        self._apply_styles()
        
    def _init_ui(self):
        self.setObjectName("SuggestionContainer")
        
        # Main Layout with Header
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # --- Header (Close Button) ---
        from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton
        header_widget = QWidget()
        header_widget.setObjectName("Header")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(10, 2, 10, 2)
        
        lbl_title = QLabel("InkSage")
        lbl_title.setObjectName("HeaderLabel")
        
        btn_close = QPushButton("×")
        btn_close.setObjectName("CloseButton")
        btn_close.setFixedSize(20, 20)
        btn_close.clicked.connect(self.hide)
        
        header_layout.addWidget(lbl_title)
        header_layout.addStretch()
        header_layout.addWidget(btn_close)
        layout.addWidget(header_widget)
        # -----------------------------
        
        self.list_widget = QListWidget()
        self.list_widget.setFocusPolicy(Qt.StrongFocus)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.itemActivated.connect(self._on_item_clicked)
        
        layout.addWidget(self.list_widget)
        self.hide()

    def _apply_styles(self):
        c_bg = config.get('ui.colors.background', '#21252b')
        c_text = config.get('ui.colors.text', '#eceff4')
        c_primary = config.get('ui.colors.primary', '#4a9eff')
        c_border = config.get('ui.colors.border', '#3b4048')
        
        self.setStyleSheet(f"""
            QWidget#SuggestionContainer {{
                background-color: {c_bg};
                border: 2px solid {c_primary};
                border-radius: 6px;
            }}
            QWidget#Header {{
                background-color: {c_border};
            }}
            QLabel#HeaderLabel {{
                color: #888; font-size: 11px; font-weight: bold;
            }}
            QPushButton#CloseButton {{
                background: transparent; color: #888; border: none; font-weight: bold;
            }}
            QPushButton#CloseButton:hover {{ color: #ff5f56; }}
            
            QListWidget {{
                background-color: {c_bg};
                border: none;
                outline: none;
                padding: 5px;
                color: {c_text};
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
            }}
            QListWidget::item {{
                padding: 10px;
                border-bottom: 1px solid {c_border};
            }}
            QListWidget::item:selected {{
                background-color: {c_primary};
                color: white;
            }}
        """)

    def set_suggestions(self, suggestions: list[str]):
        self.suggestions = suggestions
        self.list_widget.clear()
        if not suggestions:
            self.hide()
            return

        for i, text in enumerate(suggestions):
            display_text = f"{i+1}. {text}"
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, text) 
            self.list_widget.addItem(item)
            
        self.list_widget.setCurrentRow(0)
        self._resize_to_fit()

    def show_at_cursor(self):
        pos = QCursor.pos()
        screen = QGuiApplication.screenAt(pos)
        if not screen: screen = QGuiApplication.primaryScreen()
        geo = screen.availableGeometry()
        
        x = pos.x() + 15
        y = pos.y() + 20
        
        if x + self.width() > geo.right(): x = geo.right() - self.width() - 10
        if y + self.height() > geo.bottom(): y = pos.y() - self.height() - 10 
            
        self.move(x, y)
        self.show()
        self.raise_()
        self.list_widget.setFocus()
        self.activateWindow()

    def _resize_to_fit(self):
        row_height = 45
        header_height = 30
        count = self.list_widget.count()
        total_height = min((count * row_height) + header_height + 10, 500)
        self.resize(600, total_height)

    def _on_item_clicked(self, item):
        raw_text = item.data(Qt.UserRole)
        self._accept_suggestion(raw_text)

    def _accept_suggestion(self, text):
        """Copies text and triggers paste."""
        if not text: return
        
        # 🚨 KEY FIX: Insert via Clipboard Manager (Simulates Ctrl+V)
        clipboard_manager.insert_text(text)
        
        self.suggestion_selected.emit(text)
        self.hide()

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Tab):
            current = self.list_widget.currentItem()
            if current: self._accept_suggestion(current.data(Qt.UserRole))
        elif key == Qt.Key_Escape:
            self.hide()
        elif Qt.Key_1 <= key <= Qt.Key_9:
            index = key - Qt.Key_1
            if index < self.list_widget.count():
                item = self.list_widget.item(index)
                self._accept_suggestion(item.data(Qt.UserRole))
        else:
            super().keyPressEvent(event)