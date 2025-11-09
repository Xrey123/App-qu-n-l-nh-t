"""
Khởi động ứng dụng Quản lý Bán hàng với AI Agent
"""

import sys
import os

# Thêm thư mục gốc vào Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*40)
print("  KHOI DONG APP QUAN LY + AI")
print("="*40)
print()

# Kiểm tra AI System (với Permissions)
print("Đang tải AI System (Gemma2 + Permissions)...")
print("Vui lòng đợi 5-10 giây...")
print()

try:
    from ai_system import AIAssistant
    print("✅ AI System đã sẵn sàng!")
    AI_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ AI không khả dụng: {e}")
    print("💡 App vẫn chạy được, nhưng không có AI")
    AI_AVAILABLE = False

print()
print("-"*40)
print()

# Khởi động PyQt5 app
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from main_gui import DangNhap, SplashScreen
from db import khoi_tao_db

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set style
    app.setStyle("Fusion")
    
    # Show splash screen with ShopFlow branding
    splash = SplashScreen()
    splash.show()
    
    # Store login window reference globally to prevent garbage collection
    login_window = None
    
    # Initialize app components
    def init_app():
        global login_window
        
        try:
            splash.update_status("Đang khởi tạo database...")
            QApplication.processEvents()
            
            # Khởi tạo database
            try:
                khoi_tao_db()
            except Exception as e:
                print(f"⚠️ Database init warning: {e}")
            
            splash.update_status("Đang tải AI system...")
            QApplication.processEvents()
            
            # Small delay for smooth loading
            import time
            time.sleep(0.5)
            
            splash.update_status("Đang khởi động giao diện...")
            QApplication.processEvents()
            time.sleep(0.3)
            
            splash.update_status("Hoàn tất! ✅")
            QApplication.processEvents()
            time.sleep(0.2)
            
            print("\n🎯 Đang mở màn hình đăng nhập...")
            
            # Hiển thị màn hình đăng nhập
            login_window = DangNhap()
            
            # Show login window TRƯỚC
            login_window.show()
            login_window.raise_()  # Đưa lên trên cùng
            login_window.activateWindow()  # Focus vào window
            
            print("✅ Màn hình đăng nhập đã hiển thị!")
            
            # Đợi 1 chút rồi mới đóng splash
            QTimer.singleShot(500, splash.close)
            
            print("✅ Splash screen đã đóng!")
            print("="*40)
            print("  APP ĐÃ SẴN SÀNG!")
            print("="*40)
            
        except Exception as e:
            print(f"❌ Lỗi khởi động app: {e}")
            import traceback
            traceback.print_exc()
            # Close splash on error
            try:
                splash.close()
            except:
                pass
    
    # Use QTimer to run init after splash is shown
    QTimer.singleShot(100, init_app)
    
    # Chạy app
    sys.exit(app.exec_())
