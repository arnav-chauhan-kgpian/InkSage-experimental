"""
InkSage Visual Language
=======================

Manages the Qt Style Sheets (QSS) for the application.
This version enforces SOLID colors (no transparency) to ensure
maximum compatibility and visibility across all Windows configurations.
"""

from ..utils.config import config

class StyleManager:
    """
    Generates QSS dynamically.
    Forced Opaque Mode to prevent "Ghost Window" bugs.
    """
    
    def __init__(self):
        # Load base colors from config
        self.colors = config.get('ui.colors', {})
        
        # Core Palette
        self.c_primary = self.colors.get('primary', '#4a9eff')
        self.c_secondary = self.colors.get('secondary', '#45a165')
        self.c_accent = self.colors.get('accent', '#9b59b6')
        self.c_bg = self.colors.get('background', '#21252b')
        self.c_text = self.colors.get('text', '#eceff4')
        self.c_border = self.colors.get('border', '#3b4048')
        
        self.c_error = '#ff5f56'
        self.c_muted = '#8f9aab'

    def _to_rgba(self, hex_code: str, alpha: float) -> str:
        """
        FORCE OPAQUE HELPER.
        Ignores the 'alpha' argument and forces 1.0 (255) opacity.
        """
        if not hex_code.startswith('#'):
            return hex_code
        
        hex_code = hex_code.lstrip('#')
        try:
            r = int(hex_code[0:2], 16)
            g = int(hex_code[2:4], 16)
            b = int(hex_code[4:6], 16)
            # 🚨 FORCE ALPHA TO 255 (SOLID) 🚨
            return f"rgba({r}, {g}, {b}, 255)" 
        except ValueError:
            return hex_code

    @property
    def main_window(self) -> str:
        """Style for the main dashboard."""
        bg_solid = self._to_rgba(self.c_bg, 1.0)
        
        return f"""
            QWidget#CentralWidget {{
                background-color: {bg_solid};
                border: 2px solid {self.c_primary};
                border-radius: 12px;
            }}
            QLabel {{
                color: {self.c_text};
                font-family: 'Segoe UI', sans-serif;
            }}
            QLabel#Title {{
                font-size: 18px; font-weight: bold; color: {self.c_primary};
            }}
            QLabel#Status {{
                font-size: 12px; color: {self.c_muted}; margin-right: 10px;
            }}
            QPushButton#CloseButton {{
                background-color: {self.c_error};
                border-radius: 12px; border: none; color: white; font-weight: bold;
            }}
            QPushButton#BigButton {{
                background-color: {self._to_rgba(self.c_primary, 0.2)};
                border: 1px solid {self.c_primary};
                border-radius: 8px; color: {self.c_text};
                font-size: 16px; padding: 15px; text-align: left; padding-left: 20px;
            }}
            QPushButton#BigButton:hover {{
                background-color: {self.c_primary}; color: white;
            }}
            QPushButton#FeatureButton {{
                background-color: {self._to_rgba('#000000', 0.2)};
                border: 1px solid {self.c_border};
                border-radius: 6px; padding: 10px; color: {self.c_text};
            }}
            QPushButton#FeatureButton:hover {{
                background-color: {self.c_border};
            }}
        """

    @property
    def floating_widget(self) -> str:
        """Style for popups."""
        bg_solid = self._to_rgba(self.c_bg, 1.0)
        return f"""
            QDialog, QWidget {{
                background-color: {bg_solid};
                border: 1px solid {self.c_border};
                border-radius: 12px;
                color: {self.c_text};
                font-family: 'Segoe UI', sans-serif;
            }}
        """

    # --- Fallback Properties for Compatibility ---
    @property
    def primary_button(self): return self.floating_widget
    @property
    def secondary_button(self): return self.floating_widget
    @property
    def close_button(self): return self.floating_widget
    @property
    def text_edit(self): return self.floating_widget
    @property
    def progress_bar(self): return self.floating_widget
    @property
    def title_label(self): return self.floating_widget
    @property
    def label(self): return self.floating_widget
    @property
    def status_label(self): return self.floating_widget

# Global Instance
styles = StyleManager()