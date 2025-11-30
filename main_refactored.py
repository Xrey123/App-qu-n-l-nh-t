"""
Main entry point for the application
Uses refactored GUI modules
"""
import sys
from PyQt5.QtWidgets import QApplication
from gui.splash import SplashScreen
from gui.auth import DangNhap
from gui.main_window import MainWindow
from db import khoi_tao_db
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    # Initialize database
    khoi_tao_db()
    
    # Create application
    app = QApplication(sys.argv)
    
    # Show splash screen
    splash = SplashScreen()
    splash.show()
    splash.update_status("Đang khởi tạo...")
    app.processEvents()
    
    # Initialize login window
    splash.update_status("Đang tải giao diện...")
    app.processEvents()
    
    login_window = DangNhap()
    
    # Close splash and show login
    splash.update_status("Hoàn tất!")
    app.processEvents()
    
    from PyQt5.QtCore import QTimer
    QTimer.singleShot(1000, splash.close)
    QTimer.singleShot(1000, login_window.show)
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
