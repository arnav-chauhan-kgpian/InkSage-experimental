"""
InkSage System Tray
===================

Manages the background presence of the application.
Draws a custom vector icon programmatically (no external assets required).
"""

from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication, QStyle
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QAction
from PySide6.QtCore import Qt, Signal

class InkSageTray(QSystemTrayIcon):
    """
    System Tray integration.
    Allows the app to run in the background and provides a context menu.
    """
    
    # Signals to control the main application state
    show_requested = Signal()
    quit_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 1. Generate Icon
        try:
            self.setIcon(self._create_programmatic_icon())
        except Exception:
            # Fallback if drawing fails (headless/server environments)
            self.setIcon(QApplication.style().standardIcon(QStyle.SP_ComputerIcon))
        
        # 2. Setup Context Menu
        self._init_menu()
        
        # 3. Handle Interactions
        self.activated.connect(self._on_tray_click)
        self.setToolTip("InkSage - AI Context Engine")
        self.show()

    def _init_menu(self):
        menu = QMenu()
        
        # Show Action
        action_show = QAction("Show Command Bar", self)
        action_show.triggered.connect(self.show_requested.emit)
        menu.addAction(action_show)
        
        # Separator
        menu.addSeparator()
        
        # Pause Action (Toggle)
        self.action_pause = QAction("Pause Monitoring", self)
        self.action_pause.setCheckable(True)
        menu.addAction(self.action_pause)
        
        menu.addSeparator()
        
        # Quit Action
        action_quit = QAction("Quit InkSage", self)
        action_quit.triggered.connect(self.quit_requested.emit)
        menu.addAction(action_quit)
        
        self.setContextMenu(menu)

    def _on_tray_click(self, reason):
        """Handle clicking the icon directly."""
        # Trigger = Left Click, Context = Right Click
        if reason == QSystemTrayIcon.Trigger: 
            self.show_requested.emit()

    def _create_programmatic_icon(self) -> QIcon:
        """
        Draws a modern 'Spark' icon in memory.
        Avoids dependency on external .png/.ico files.
        """
        size = 64
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Colors (Ink Blue & Sparkle Purple)
        c_primary = QColor("#4a9eff")
        c_accent = QColor("#9b59b6")
        
        # Draw a stylized "Ink Drop"
        painter.setBrush(c_primary)
        painter.setPen(Qt.NoPen)
        
        # Main Circle (The Drop)
        painter.drawEllipse(16, 16, 32, 32)
        
        # The "Spark" (Top right accent)
        painter.setBrush(c_accent)
        painter.drawEllipse(40, 10, 14, 14)
        
        painter.end()
        return QIcon(pixmap)