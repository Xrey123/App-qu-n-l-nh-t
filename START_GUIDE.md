# 🚀 HƯỚNG DẪN KHỞI ĐỘNG SHOPFLOW

## ✅ CÁCH CHẠY ĐÚNG

```bash
python start.py
```

**Lý do:**
- `start.py` khởi động **AI System** (Gemma2 + Permissions) cùng với giao diện
- Load splash screen với logo ShopFlow
- Khởi tạo database tự động
- Tích hợp đầy đủ chức năng AI Assistant

---

## ❌ KHÔNG CHẠY TRỰC TIẾP

```bash
# SAI - Thiếu AI System
python main_gui.py
```

Chạy trực tiếp `main_gui.py` sẽ:
- ❌ Thiếu AI Agent (không thể chat với AI)
- ❌ Thiếu khởi tạo AI permissions
- ⚠️ Chỉ dùng để test giao diện đơn lẻ

---

## 📋 YÊU CẦU HỆ THỐNG

### Thư viện Python:
```bash
pip install PyQt5 pandas openpyxl ollama groq
```

### AI System (Optional):
- **Online Mode**: Groq API (miễn phí, nhanh)
- **Offline Mode**: Ollama + Phi3:mini
  ```bash
  ollama pull phi3:mini
  ```

---

## 🎨 TÍNH NĂNG MỚI (Version 2.5.0)

### 1. Splash Screen 🌟
- Logo ShopFlow với animation
- Progress bar loading
- Gradient background đẹp mắt

### 2. Tên App Mới
- **ShopFlow** - Quản lý bán hàng thông minh
- Tên viết tắt: **SF**

### 3. Cột Sản Phẩm Tự Động Stretch
- Hiển thị đầy đủ tên sản phẩm
- Các cột khác tự động thu nhỏ

### 4. Tab Cài Đặt Chia 2 Phần
- 🤖 **AI Settings**: Cấu hình Groq API
- ℹ️ **Information**: Version app, tính năng

### 5. Thứ Tự Tab Tối Ưu
- Tab "Cài đặt" di chuyển ra cuối
- Workflow hợp lý hơn

---

## 🔧 TROUBLESHOOTING

### Lỗi: "ModuleNotFoundError: No module named 'ai_system'"
```bash
# Kiểm tra thư mục ai_offline_pro
ls src/ai_offline_pro/

# Nếu thiếu, tạo file __init__.py
touch src/ai_offline_pro/__init__.py
```

### Lỗi: "Ollama not running"
```bash
# Khởi động Ollama
ollama serve

# Pull model (terminal khác)
ollama pull phi3:mini
```

### Lỗi: Splash screen không hiện
```bash
# Kiểm tra file logo.png
ls logo.png

# Nếu không có, app sẽ dùng emoji 🛒 thay thế
```

---

## 📞 HỖ TRỢ

- **Email**: support@shopflow.vn
- **Website**: www.shopflow.vn
- **Version**: 2.5.0
- **Ngày cập nhật**: 08.11.2024

---

## 📄 TÀI LIỆU KHÁC

- `UPDATE_UI_IMPROVEMENTS.md` - Chi tiết cập nhật giao diện
- `HUONG_DAN_GROQ_API.md` - Hướng dẫn lấy Groq API key
- `AI_ACTIONS_README.md` - Tài liệu AI features
- `SHORTCUTS_GUIDE.md` - Phím tắt

---

**Chúc bạn sử dụng ShopFlow hiệu quả! 🎉**
