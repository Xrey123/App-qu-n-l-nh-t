# 📁 CẤU TRÚC DỰ ÁN - HỆ THỐNG QUẢN LÝ CỬA HÀNG NHỚT

## 🎯 **FILE CHÍNH**

```
📄 main_gui.py (8389 dòng)    ⭐ App GUI chính
📄 RUN_GUI.bat                 ⭐ Mở app nhanh nhất
📄 db.py                       🔧 Khởi tạo database
📄 fapp.db                     💾 Database SQLite
📄 requirements.txt            📦 Dependencies
```

---

## 📚 **THƯ VIỆN HELPER (Không chạy trực tiếp)**

```
📄 invoices.py    - Xử lý hóa đơn
📄 products.py    - Quản lý sản phẩm
📄 users.py       - Quản lý user
📄 stock.py       - Quản lý kho
📄 reports.py     - Báo cáo
📄 shortcuts.py   - Phím tắt
```

---

## 📂 **THƯ MỤC QUAN TRỌNG**

```
📁 ai/                     - Knowledge base cho AI
   ├── app_knowledge.json            (basic - 308 dòng)
   ├── app_knowledge_enhanced.json   (enhanced - 900 dòng) ⭐
   ├── db_queries.json               (SQL queries cho AI)
   └── config.json                   (Groq API key)

📁 ai_system/              - Hệ thống AI
   ├── hybrid.py                     (Groq + Phi3)
   ├── actions.py                    (AI actions)
   └── permissions.py                (Phân quyền AI)

📁 utils/                  - Utilities
   ├── db_connection.py              (Kết nối DB)
   ├── db_helpers.py                 (DB helpers)
   ├── invoice.py                    (Invoice utils)
   ├── money.py                      (Xử lý tiền)
   └── zalo_notification.py          (Zalo API)

📁 data_export/            - Export dữ liệu
   ├── nhan_hang/                    (CSV nhận hàng)
   └── tong_ket_ca/                  (Tổng kết ca)

📁 .venv/                  - Python virtual environment
📁 logs/                   - Log files
📁 scripts/                - Scripts tiện ích
```

---

## 📄 **TÀI LIỆU (File .md)**

```
📄 HOW_TO_OPEN_APP.md              ⭐ Hướng dẫn mở app
📄 TEST_AUTO_TAB_SWITCHING.md      🧪 Test tự động chuyển tab
📄 START_GUIDE.md                  📖 Hướng dẫn bắt đầu
📄 AI_CAPABILITIES_COMPLETE.md     🤖 Khả năng AI
📄 AI_QUICK_REFERENCE.md           🤖 Tham khảo nhanh AI
📄 HUONG_DAN_GROQ_API.md          🔑 Setup Groq API
📄 ZALO_INTEGRATION_SUMMARY.md     📱 Tích hợp Zalo
```

---

## 🗑️ **FILE CÓ THỂ XÓA** (Đã cũ/Không dùng)

### **Demo/Test Files (5 files)**
```
❌ demo_ai_features.py
❌ demo_chi_tiet_ban.py
❌ test_ai_database_security.py
❌ test_direct_db_query.py
❌ test_zalo_notification.py
```

### **Migration Scripts (4 files)** - Đã chạy xong
```
❌ migration_add_phone.py
❌ update_user_phones.py
❌ quick_update_phones.py
❌ fix_debug_prints.py
```

### **Old Batch Files (2 files)**
```
❌ START_APP_SIMPLE.bat        (Dùng Ollama, giờ dùng Groq)
❌ CLEANUP_FINAL_COMPLETE.bat  (Script cũ)
```

### **Optional**
```
⚠️ llama.cpp/                  (Chỉ cần nếu dùng offline AI)
⚠️ start.py                    (CLI training, không phải GUI)
```

**→ Chạy `CLEANUP_OLD_FILES.bat` để xóa/backup tự động**

---

## 🚀 **WORKFLOW PHÁT TRIỂN**

### **1. Khởi động app:**
```
RUN_GUI.bat
```

### **2. Edit code:**
```
- main_gui.py          → GUI chính
- ai_system/hybrid.py  → Logic AI
- ai/app_knowledge_enhanced.json → Knowledge base
```

### **3. Commit changes:**
```cmd
git add .
git commit -m "Update..."
push.bat
```

---

## 📊 **THỐNG KÊ DỰ ÁN**

| Loại | Số lượng | Ghi chú |
|------|----------|---------|
| **File Python chính** | 6 | main_gui, db, helpers |
| **File helper .py** | 6 | invoices, products, users, stock, reports, shortcuts |
| **File AI system** | 3 | hybrid, actions, permissions |
| **File utils** | 6 | db_connection, db_helpers, invoice, money, zalo, logging |
| **File tài liệu .md** | 15+ | Hướng dẫn, documentation |
| **File có thể xóa** | 11 | Demo, test, migration cũ |
| **Dòng code chính** | ~8500 | main_gui.py |

---

## ⚡ **QUICK COMMANDS**

### **Mở app:**
```cmd
RUN_GUI.bat
```

### **Init database:**
```cmd
python db.py
```

### **Cleanup old files:**
```cmd
CLEANUP_OLD_FILES.bat
```

### **Git push:**
```cmd
push.bat
```

### **Git pull:**
```cmd
pull.bat
```

---

## 🎯 **1 LỆNH DUY NHẤT ĐỂ MỞ APP**

```
RUN_GUI.bat
```

**Thế thôi!** 🚀
