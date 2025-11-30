"""
Tab Settings - Placeholder cho cấu hình AI Agent (sẽ thiết kế lại sau)
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTabWidget
from PyQt5.QtCore import Qt


class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """⚙️ Settings Tab - Cấu hình AI và Information"""
        # Create sub-tabs for Settings
        settings_tabs = QTabWidget()
        
        # Tab 1: AI Settings (Placeholder)
        tab_ai_settings = QWidget()
        ai_layout = QVBoxLayout()
        lbl =QLabel("<h2>🤖 AI Settings</h2><p>Phần cấu hình AI Agent sẽ được thiết kế lại trong tương lai.</p>")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setWordWrap(True)
        ai_layout.addWidget(lbl)
        ai_layout.addStretch()
        tab_ai_settings.setLayout(ai_layout)
        settings_tabs.addTab(tab_ai_settings, "🤖 AI Settings")
        
        # Tab 2: Information (Placeholder)
        tab_info = QWidget()
        info_layout = QVBoxLayout()
        info_lbl = QLabel("<h2>ℹ️ Information</h2><p>Thông tin hệ thống và phiên bản.</p>")
        info_lbl.setAlignment(Qt.AlignCenter)
        info_lbl.setWordWrap(True)
        info_layout.addWidget(info_lbl)
        info_layout.addStretch()
        tab_info.setLayout(info_layout)
        settings_tabs.addTab(tab_info, "ℹ️ Information")
        
        # Set main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(settings_tabs)
        self.setLayout(main_layout)
