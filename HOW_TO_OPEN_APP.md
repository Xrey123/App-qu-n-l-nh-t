# 🗂️ CÁC FILE MỞ APP - HƯỚNG DẪN

## ✅ **FILE CHÍNH ĐỂ MỞ APP**

### **1. RUN_GUI.bat** ⭐ (KHUYẾN NGHỊ)
**Mục đích:** Mở GUI app nhanh nhất
**Cách dùng:** Double-click file
```cmd
RUN_GUI.bat
```

### **2. main_gui.py**
**Mục đích:** File Python chính của app
**Cách dùng:** Chạy bằng Python
```cmd
python main_gui.py
# hoặc
.venv\Scripts\python.exe main_gui.py
```

### **3. db.py**
**Mục đích:** Khởi tạo database lần đầu
**Cách dùng:** Chỉ chạy 1 lần khi setup
```cmd
python db.py
```

---

## ❌ **FILE KHÔNG NÊN DÙNG ĐỂ MỞ APP**

### **start.py**
- ❌ Chỉ hiện hướng dẫn Auto Trainer
- ❌ KHÔNG mở GUI app
- Dùng cho: CLI training AI (không phải GUI)

### **START_APP_SIMPLE.bat**
- ❌ File cũ, dùng cho Ollama/Gemma (offline AI)
- ❌ Hiện tại dùng Groq API, không cần file này
- Đề xuất: Xóa hoặc backup

---

## 📊 **TÓM TẮT**

| File | Dùng để mở GUI? | Ghi chú |
|------|----------------|---------|
| ✅ **RUN_GUI.bat** | **CÓ** | **KHUYẾN NGHỊ - Nhanh nhất** |
| ✅ **main_gui.py** | **CÓ** | File Python chính |
| ⚠️ **db.py** | Không | Chỉ init DB lần đầu |
| ❌ **start.py** | Không | CLI training, không phải GUI |
| ❌ **START_APP_SIMPLE.bat** | Không | Cũ, dùng Ollama (không cần) |

---

## 🧹 **CLEANUP FILE DƯ THỪA**

Nếu muốn xóa các file demo/test/migration cũ:

```cmd
CLEANUP_OLD_FILES.bat
```

File này sẽ:
1. ✅ Backup tất cả file vào `backup_old_files/`
2. ✅ Xóa các file demo, test, migration
3. ✅ Xóa file batch cũ không dùng

**Các file sẽ được xóa:**
- `demo_*.py` (2 files)
- `test_*.py` (3 files)
- `*migration*.py`, `*update*.py`, `fix_*.py` (4 files)
- `START_APP_SIMPLE.bat`, `CLEANUP_FINAL_COMPLETE.bat` (2 files)

**Tổng:** 11 files dư thừa

---

## 🚀 **CÁCH MỞ APP NHANH NHẤT**

### **Cách 1: Double-click (KHUYẾN NGHỊ)**
```
Tìm file: RUN_GUI.bat
→ Double-click
→ App mở ngay
```

### **Cách 2: Terminal/CMD**
```cmd
cd "d:\f app"
RUN_GUI.bat
```

### **Cách 3: Python trực tiếp**
```cmd
cd "d:\f app"
.venv\Scripts\python.exe main_gui.py
```

---

## 📝 **GHI CHÚ**

- Tất cả file `.md` là tài liệu, không ảnh hưởng đến app
- Thư mục `llama.cpp/` chỉ cần nếu dùng offline AI (hiện dùng Groq)
- File `shortcuts.py` là phím tắt (optional)
