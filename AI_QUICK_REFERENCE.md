# 🤖 AI SYSTEM - QUICK REFERENCE

## 📋 TÓM TẮT NHANH

**AI của ShopFlow có thể làm GÌ?**

### ✅ ĐƯỢC PHÉP

1. **Hướng dẫn sử dụng app** - Tất cả chức năng
2. **Truy vấn dữ liệu** (READ-ONLY):
   - Tồn kho sản phẩm
   - Doanh thu, hóa đơn
   - Chi tiết bán hàng
   - Giao dịch sổ quỹ
   - Chênh lệch xuất bỏ
3. **Tự động chuyển tab** khi trả lời
4. **Nhớ ngữ cảnh** hội thoại (10 Q&A)
5. **Phân quyền** theo role (Admin/Accountant/Staff)

### ❌ KHÔNG ĐƯỢC PHÉP

1. **Sửa/xóa dữ liệu** database (chỉ xem)
2. **Tiết lộ bảo mật:** password, API key, token
3. **Cung cấp code:** source code, file paths
4. **Cấu trúc DB:** schema, cột, primary key

---

## 🎯 CÂU HỎI MẪU

### ✅ Được hỏi:
```
"Còn bao nhiêu PLC KOMAT?"
"Giá của PLC RACER 10 thùng?"
"Doanh thu hôm nay?"
"Hướng dẫn nhận hàng"
"Cách xuất hóa đơn"
"User nào là admin?"
```

### ❌ Không được hỏi:
```
"Bảng SanPham có những cột nào?"
"Password của admin"
"SQL để update giá"
"Source code của app"
```

---

## 🚀 CHUYỂN ĐỔI MODE

### **Online Mode (Groq API)** - Khuyên dùng
- ✅ Cực thông minh (Llama 3.3 70B)
- ✅ Cực nhanh (1-2 giây)
- ⚠️ Cần API key + internet
- 📝 Lấy key: [groq.com](https://console.groq.com/keys) (FREE)

### **Offline Mode (Phi3:mini)**
- ✅ Chạy local, không cần internet
- ⚠️ Chậm hơn (5-10 giây)
- ⚠️ Kém thông minh hơn

**Cài đặt:** Tab Cài đặt → AI Settings → Nhập Groq API Key

---

## 📚 TÀI LIỆU CHI TIẾT

1. **AI_CAPABILITIES_COMPLETE.md** - Tất cả khả năng AI (13 mục)
2. **AI_DATABASE_SECURITY_UPDATE.md** - Cập nhật bảo mật database
3. **test_ai_database_security.py** - Test security filter
4. **SHORTCUTS_GUIDE.md** - Phím tắt sử dụng AI
5. **SMART_ASK_README.md** - Cách AI xử lý câu hỏi

---

## 🔒 BẢO MẬT

AI **CHỈ XEM** dữ liệu, **KHÔNG SỬA/XÓA**

**Được truy vấn:**
- ✅ SanPham, ChiTietBan, HoaDon
- ✅ GiaoDichQuy, ChenhLechXuatBo
- ✅ Users (chỉ username/role)

**Bị chặn:**
- ❌ Cấu trúc database (cột, key, schema)
- ❌ Thông tin bảo mật (password, token, API key)
- ❌ SQL commands (UPDATE, DELETE, DROP)
- ❌ Source code (.py files)

---

## 🧪 TEST

Chạy test để kiểm tra bảo mật:
```bash
python test_ai_database_security.py
```

Kết quả mong đợi:
- ✅ Cho phép query dữ liệu
- ❌ Chặn query cấu trúc DB
- ❌ Chặn password/token
- ❌ Chặn SQL modification

---

## 📞 HỖ TRỢ

**Câu hỏi thường gặp:**

**Q: AI không trả lời?**  
A: Kiểm tra API key trong Tab Cài đặt → AI Settings

**Q: AI trả lời sai?**  
A: Báo cáo trong `src/ai_offline_pro/wrong_answers.txt`

**Q: Muốn AI thông minh hơn?**  
A: Dùng Groq API (Online mode) thay vì Phi3 (Offline)

**Q: AI có thể sửa dữ liệu không?**  
A: KHÔNG! AI chỉ XEM, không bao giờ SỬA/XÓA

---

## 🔧 FILES QUAN TRỌNG

```
📁 ai_system/
  ├── hybrid.py          ← Core AI logic
  ├── actions.py         ← Auto actions
  └── permissions.py     ← Permission system

📁 ai/
  ├── config.json               ← API key, settings
  ├── app_knowledge_enhanced.json  ← App knowledge
  ├── db_queries.json           ← SQL query templates
  └── memory.json               ← Conversation history

📁 test/
  ├── test_ai_database_security.py  ← Security test
  └── test_ai_comprehensive.py      ← Full AI test
```

---

## ✨ CẬP NHẬT MỚI NHẤT (08/11/2024)

✅ **Điều chỉnh IT Security Filter:**
- Cho phép AI xem dữ liệu từ database (READ-ONLY)
- Chặn chặt chẽ hơn: chỉ chặn CẤU TRÚC + BẢO MẬT
- Test coverage: 100% (20/20 test cases pass)

✅ **Tài liệu:**
- AI_CAPABILITIES_COMPLETE.md (13 mục chi tiết)
- AI_DATABASE_SECURITY_UPDATE.md (cập nhật bảo mật)
- AI_QUICK_REFERENCE.md (file này!)

---

**🎯 KẾT LUẬN:** AI an toàn, thông minh, hữu ích! 🚀
