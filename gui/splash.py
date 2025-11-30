import os
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QProgressBar, QApplication, QDesktopWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

class SplashScreen(QWidget):
    """Màn hình loading với logo và animation"""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Set size
        self.setFixedSize(500, 400)

        # Center on screen
        screen = QDesktopWidget().screenGeometry()
        self.move(
            (screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2
        )

        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)

        # Background frame
        frame = QWidget()
        frame.setStyleSheet(
            """
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 20px;
            }
        """
        )
        frame_layout = QVBoxLayout()
        frame_layout.setSpacing(20)

        # Logo
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignCenter)
        try:
            # Adjust path to find logo in parent directory
            base_dir = os.path.dirname(os.path.dirname(__file__))
            logo_path = os.path.join(base_dir, "logo.png")
            if os.path.exists(logo_path):
                pixmap = QPixmap(logo_path).scaled(
                    120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                logo_label.setPixmap(pixmap)
            else:
                # Fallback to text logo
                logo_label.setText("🛒")
                logo_label.setStyleSheet("font-size: 80px;")
        except Exception as e:
            print(f"Logo loading error: {e}")
            logo_label.setText("🛒")
            logo_label.setStyleSheet("font-size: 80px;")

        frame_layout.addWidget(logo_label)

        # App name
        app_name = QLabel("ShopFlow")
        app_name.setAlignment(Qt.AlignCenter)
        app_name.setStyleSheet(
            """
            font-size: 36px;
            font-weight: bold;
            color: white;
            margin: 10px;
        """
        )
        frame_layout.addWidget(app_name)

        # Subtitle
        subtitle = QLabel("Quản lý bán hàng thông minh")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(
            """
            font-size: 14px;
            color: rgba(255, 255, 255, 0.9);
            margin-bottom: 20px;
        """
        )
        frame_layout.addWidget(subtitle)

        # Loading animation (progress bar)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminate mode
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(4)
        self.progress.setStyleSheet(
            """
            QProgressBar {
                background: rgba(255, 255, 255, 0.2);
                border: none;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background: white;
                border-radius: 2px;
            }
        """
        )
        frame_layout.addWidget(self.progress)

        # Loading text
        self.status_label = QLabel("Đang khởi tạo...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(
            """
            font-size: 12px;
            color: rgba(255, 255, 255, 0.8);
            margin-top: 10px;
        """
        )
        frame_layout.addWidget(self.status_label)

        frame_layout.addStretch()
        frame.setLayout(frame_layout)
        layout.addWidget(frame)
        self.setLayout(layout)

    def update_status(self, text):
        """Update loading status text"""
        self.status_label.setText(text)
        QApplication.processEvents()
