import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from users import dang_nhap
from gui.main_window import MainWindow

class DangNhap(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Đăng nhập")
        
        # ✅ Set Window Icon cho cửa sổ đăng nhập
        try:
            base_dir = os.path.dirname(os.path.dirname(__file__))
            logo_path = os.path.join(base_dir, "logo.png")
            if os.path.exists(logo_path):
                self.setWindowIcon(QIcon(logo_path))
        except Exception as e:
            print(f"Không thể load logo: {e}")
        
        self.resize(380, 480)
        
        # === CLEAN MODERN LOGIN DESIGN ===
        self.setStyleSheet(
            """
            QWidget { background: white; font-family: Arial; }
            QLabel { color: black; font-size: 10pt; }
            QLineEdit { font-size: 10pt; background: white; color: black; border: 1px solid #ccc; border-radius: 2px; padding: 4px; }
            QPushButton { font-size: 10pt; background: #e0e0e0; color: black; border: 1px solid #ccc; border-radius: 2px; padding: 6px 12px; }
            QPushButton:hover { background: #d0d0d0; }
        """
        )
        
        # Main container
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(0)
        
        card = QWidget()
        card.setMaximumWidth(340)
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(12)
        
        # Logo
        try:
            logo_label = QLabel()
            base_dir = os.path.dirname(os.path.dirname(__file__))
            logo_path = os.path.join(base_dir, "logo.png")
            if os.path.exists(logo_path):
                logo_pixmap = QPixmap(logo_path)
                logo_scaled = logo_pixmap.scaled(
                    100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                logo_label.setPixmap(logo_scaled)
            logo_label.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(logo_label)
        except Exception as e:
            print(f"Không thể hiển thị logo: {e}")
        
        # Username field
        self.txt_username = QLineEdit()
        self.txt_username.setPlaceholderText("Tên đăng nhập")
        card_layout.addWidget(self.txt_username)
        
        card_layout.addSpacing(12)
        
        # Password field
        self.txt_password = QLineEdit()
        self.txt_password.setEchoMode(QLineEdit.Password)
        self.txt_password.setPlaceholderText("Mật khẩu")
        card_layout.addWidget(self.txt_password)
        
        card_layout.addSpacing(16)
        
        # Login button
        btn = QPushButton("ĐĂNG NHẬP")
        btn.clicked.connect(self.dang_nhap_click)
        btn.setCursor(Qt.PointingHandCursor)
        card_layout.addWidget(btn)
        
        card.setLayout(card_layout)
        
        # Center card in window
        h_layout = QHBoxLayout()
        h_layout.addStretch()
        h_layout.addWidget(card)
        h_layout.addStretch()
        
        main_layout.addStretch()
        main_layout.addLayout(h_layout)
        main_layout.addStretch()
        
        self.setLayout(main_layout)
    
    def dang_nhap_click(self):
        username = self.txt_username.text()
        password = self.txt_password.text()
        result = dang_nhap(username, password)
        if result:
            user_id, role = result
            QMessageBox.information(self, "Thành công", f"Đăng nhập thành công!\nRole: {role}")
            self.hide()
            # Create and show MainWindow
            self.main_window = MainWindow(user_id, role, self)
            self.main_window.show()
        else:
            QMessageBox.warning(self, "Lỗi", "Sai tên đăng nhập hoặc mật khẩu")
