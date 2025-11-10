# 🤖 TỔNG HỢP KHẢ NĂNG AI - SHOPFLOW 2.5.0

**Cập nhật:** 08/11/2024  
**AI System:** Groq API (Llama 3.3 70B) + Phi3:mini Offline

---

## 🌟 TỔNG QUAN HỆ THỐNG AI

ShopFlow sử dụng **Hybrid AI System** với 2 chế độ:

### **🚀 ONLINE MODE - Groq API (Llama 3.3 70B)**

- **Cực thông minh:** Hiểu ngữ cảnh phức tạp
- **Cực nhanh:** Trả lời trong 1-2 giây
- **Yêu cầu:** API key (free tại groq.com) + internet

### **💻 OFFLINE MODE - Phi3:mini + RAG**

- **Chạy local:** Không cần internet
- **Dùng RAG:** Retrieval Augmented Generation
- **Tra cứu:** Database + app_knowledge.json
- **Tốc độ:** Chậm hơn nhưng vẫn ổn

---

## 📚 1. KIẾN THỨC VỀ ỨNG DỤNG

AI biết **TẤT CẢ** về ShopFlow từ `ai/app_knowledge_enhanced.json`:

### **Thông tin App**

✅ Tên: ShopFlow - Quản lý bán hàng thông minh  
✅ Phiên bản: 2.5.0 (SF)  
✅ Ngày: 08/11/2024  
✅ Công nghệ: PyQt5, SQLite (fapp.db)  
✅ Khởi động: `python start.py`

### **13 Tabs Chính**

1. 🏠 **Trang chủ** - Dashboard, thống kê
2. 📦 **Sản phẩm** - Quản lý nhớt (Admin/Accountant)
3. 📊 **Lịch sử giá** - Theo dõi thay đổi giá
4. 🛒 **Ca bán hàng** → Nhận hàng (kiểm kê) + Bán hàng
5. 📋 **Chi tiết bán** - Lịch sử bán hàng
6. 📄 **Hóa đơn** - Quản lý hóa đơn
7. 📈 **Báo cáo** - Doanh thu, lợi nhuận, tổng kết ca
8. 🤖 **AI Agent** - Chat với AI (tab này!)
9. 👥 **User** - Quản lý user (Admin only)
10. ⚖️ **Chênh lệch** - Chênh lệch xuất bỏ
11. 📤 **Xuất bỏ** - Xuất sản phẩm đã bán
12. 💰 **Công đoàn** - Tiền chênh lệch
13. 💵 **Sổ quỹ** - Giao dịch tiền

### **Quy trình Bán hàng**

```
1. Nhận hàng (đầu ca) → Kiểm kê tồn kho, ghi chênh lệch
2. Bán hàng → Nhập đơn, tính giá tự động (lẻ/buôn/VIP)
3. Tổng kết ca (cuối ca) → In báo cáo, đóng ca
```

### **Cách tính giá**

- **Giá lẻ:** SL < ngưỡng buôn (vd: < 5 thùng)
- **Giá buôn:** SL ≥ ngưỡng buôn (vd: ≥ 5 thùng)
- **Giá VIP:** Khách hàng VIP (lưu trong DB)

---

## 🔐 2. HỆ THỐNG BẢO MẬT & PHÂN QUYỀN

### **Permission System**

AI kiểm tra quyền user trước khi trả lời:

| Role              | Tabs                                                             | Actions                                 |
| ----------------- | ---------------------------------------------------------------- | --------------------------------------- |
| **Admin** 👑      | Toàn bộ 13 tabs                                                  | Tất cả                                  |
| **Accountant** 👔 | 11 tabs (trừ User, AI Agent)                                     | Xem báo cáo, xuất bỏ, công đoàn, sổ quỹ |
| **Staff** 👤      | 5 tabs (Trang chủ, Ca bán hàng, Chi tiết bán, Hóa đơn, AI Agent) | CHỈ bán hàng                            |

**Ví dụ:**

```
Staff hỏi: "Tab sản phẩm làm gì?"
AI: "🚫 Xin lỗi, tab Sản phẩm chỉ dành cho Admin hoặc Accountant..."
```

### **IT Security Filter**

AI chặn **50+ từ khóa nhạy cảm:**

#### ✅ **CHO PHÉP XEM:**

- Dữ liệu từ bảng: SanPham, ChiTietBan, HoaDon, GiaoDichQuy, ChenhLechXuatBo
- Thông tin Users: username, role (KHÔNG password)
- Các câu hỏi: "bao nhiêu", "còn", "danh sách", "tổng", "giá"

#### ❌ **CHẶN HOÀN TOÀN:**

- **Cấu trúc DB:** schema, cột, primary key, foreign key, table structure
- **Bảo mật:** password, api key, token, hash, secret
- **SQL Commands:** UPDATE, DELETE, DROP, INSERT, ALTER
- **Code:** .py files, source code, file paths, system architecture

**Ví dụ:**

```
User: "Bảng SanPham có những cột nào?"
AI: "🔒 Xin lỗi, tôi không thể cung cấp thông tin về kỹ thuật hệ thống..."

User: "Password của admin"
AI: "🔒 Xin lỗi, tôi không thể cung cấp thông tin về bảo mật..."
```

---

## 🎯 3. AUTO TAB SWITCHING

AI **tự động chuyển tab** khi trả lời về tab đó!

**13 tabs được map:**

```python
"trang chủ" → Tab 0
"sản phẩm" → Tab 1 (Admin/Accountant)
"ca bán hàng" → Tab 3
"nhận hàng" → Tab 3, Sub-tab 0
"bán hàng" → Tab 3, Sub-tab 1
"chi tiết bán" → Tab 4
"hóa đơn" → Tab 5
"báo cáo" → Tab 6
"cài đặt" → Tab 7
...
```

**Ví dụ:**

```
User: "Hướng dẫn nhận hàng"
AI: "📌 Tab Ca bán hàng → Sub-tab Nhận hàng..."
→ App TỰ ĐỘNG CHUYỂN đến tab Nhận hàng!
```

---

## 🧠 4. CONTEXT MEMORY

AI nhớ **10 cặp Q&A** gần nhất để hiểu ngữ cảnh:

```
User: "Còn bao nhiêu PLC KOMAT?"
AI: "Còn 150 thùng PLC KOMAT 2T"

User: "Giá bao nhiêu?"  ← AI hiểu "giá" là giá PLC KOMAT
AI: "Giá lẻ: 180.000, Giá buôn: 170.000, Giá VIP: 165.000"

User: "Còn cái kia thì sao?"  ← AI hiểu "cái kia" là sản phẩm khác
AI: "Bạn muốn hỏi về sản phẩm nào? PLC RACER, PLC CARTER...?"
```

---

## 📊 5. DATABASE QUERY (READ-ONLY)

AI có thể **XEM** dữ liệu từ database (an toàn, chỉ đọc):

### **Các bảng được phép truy vấn:**

| Bảng                | AI có thể xem                              |
| ------------------- | ------------------------------------------ |
| **SanPham**         | ✅ Tên, giá lẻ, giá buôn, giá VIP, tồn kho |
| **ChiTietBan**      | ✅ Sản phẩm đã bán, số lượng, giá, ngày    |
| **HoaDon**          | ✅ ID hóa đơn, khách hàng, tổng tiền, ngày |
| **GiaoDichQuy**     | ✅ User chuyển/nhận, số tiền, ghi chú      |
| **ChenhLechXuatBo** | ✅ Chênh lệch công đoạn, user, sản phẩm    |
| **DauKyXuatBo**     | ✅ Sản phẩm đầu kỳ chưa xuất hóa đơn       |
| **Users**           | ⚠️ CHỈ username, role (KHÔNG password)     |

### **Ví dụ Query:**

```
User: "Còn bao nhiêu PLC KOMAT 2T?"
AI: → Query: SELECT ton_kho FROM SanPham WHERE ten LIKE '%PLC KOMAT 2T%'
    → Trả lời: "📦 Còn 150 thùng PLC KOMAT 2T"

User: "Danh sách sản phẩm"
AI: → Query: SELECT ten, ton_kho, don_vi FROM SanPham
    → Trả lời: "📦 Sản phẩm trong kho:
                • PLC KOMAT 2T: 150 thùng
                • PLC RACER 3T: 80 thùng
                • ..."

User: "Tổng doanh thu hôm nay"
AI: → Query: SELECT SUM(tong_tien) FROM HoaDon WHERE date(ngay) = date('now')
    → Trả lời: "💰 Doanh thu hôm nay: 5.420.000 VNĐ"
```

---

## 📖 6. APP KNOWLEDGE

AI biết **chi tiết từng chức năng** từ `ai/app_knowledge_enhanced.json`:

### **Ví dụ kiến thức:**

**Nhận hàng:**

```
✅ Mục đích: Kiểm kê tồn kho đầu ca
✅ Cách dùng:
   1. Ấn "Tải danh sách sản phẩm"
   2. Nhập SL đếm được
   3. Ghi lý do nếu có chênh lệch
   4. Ấn "Xác nhận nhận hàng"
✅ Lưu ý: Phải nhận hàng trước khi bán!
```

**Bán hàng:**

```
✅ Tính giá tự động:
   - Nhập SL < 5 → Giá lẻ
   - Nhập SL ≥ 5 → Giá buôn
   - Khách VIP → Giá VIP (tự động check DB)
✅ Giảm giá: Nhập vào cột "Giảm"
✅ Xuất HĐ: Tick checkbox "XHĐ"
```

---

## 🎨 7. AI EMOTIONS (Cảm xúc AI)

AI phản ứng theo ngữ cảnh:

### **Vui vẻ:**

```
User: "AI giỏi quá!"
AI: "😊 Cảm ơn bạn! Mình luôn cố gắng hỗ trợ tốt nhất!"
```

### **Xin lỗi:**

```
User: "Sao lại sai?"
AI: "😔 Xin lỗi, để mình kiểm tra lại..."
```

### **Hài hước:**

```
User: "AI có thể yêu không?"
AI: "💕 Mình có thể yêu... yêu việc giúp bạn quản lý cửa hàng! 😄"
```

---

## 🚀 8. AUTO ACTIONS (Hành động tự động)

AI có thể **thực thi hành động** trong app:

### **Các action được hỗ trợ:**

| Action            | Mô tả            | Ví dụ                    |
| ----------------- | ---------------- | ------------------------ |
| `switch_tab`      | Chuyển tab       | "Mở tab Sản phẩm"        |
| `search_product`  | Tìm sản phẩm     | "Tìm PLC KOMAT"          |
| `show_report`     | Hiển thị báo cáo | "Báo cáo doanh thu"      |
| `calculate_price` | Tính giá         | "Giá 10 thùng PLC KOMAT" |

**Ví dụ:**

```
User: "Mở tab Sản phẩm"
AI: → Action: switch_tab(1)
    → "✅ Đã chuyển đến tab Sản phẩm"

User: "Tìm PLC KOMAT"
AI: → Action: search_product("PLC KOMAT")
    → "🔍 Tìm thấy 3 sản phẩm: PLC KOMAT 2T, 3T, 5T"
```

---

## 📝 9. AUTO TRAINING (Tự học)

AI có thể **học từ câu hỏi sai**:

### **File:** `src/ai_offline_pro/wrong_answers.txt`

```
Q: Giá PLC KOMAT 10 thùng?
Wrong A: Giá lẻ 180.000
Right A: Giá buôn 170.000 (vì ≥5 thùng)
---
```

### **Tools:**

- `auto_trainer.py` - Tự động train từ wrong_answers.txt
- `fix_all_wrong_answers.py` - Sửa tất cả lỗi
- `delete_wrong_answers.py` - Xóa lỗi đã fix

---

## 🧪 10. SMART ASK (Hỏi thông minh)

File: `smart_ask.py`

AI phân tích câu hỏi theo **6 bước:**

```
1. 🔍 Normalize - Chuẩn hóa câu hỏi
2. 🔐 Permission - Kiểm tra quyền
3. 🛡️ Security - Lọc IT keywords
4. 🗄️ Database - Query data (nếu cần)
5. 📚 Knowledge - Tra app_knowledge
6. 🤖 AI - Hỏi Groq/Phi3
```

**Ví dụ flow:**

```
User: "Còn bao nhiêu PLC KOMAT?" (Staff)
→ Step 1: Normalize ✅
→ Step 2: Permission ✅ (Staff được hỏi về tồn kho)
→ Step 3: Security ✅ (không có IT keywords)
→ Step 4: Database ✅ (Query: SELECT ton_kho...)
→ Step 5: Skip (đã có kết quả từ DB)
→ Step 6: Skip
→ Answer: "📦 Còn 150 thùng PLC KOMAT 2T"
```

---

## 🎯 11. USE CASES (Trường hợp sử dụng)

### **👤 Staff (Nhân viên bán hàng)**

```
✅ "Hướng dẫn nhận hàng"
✅ "Cách bán hàng"
✅ "Giá PLC KOMAT 10 thùng" → AI tính: Giá buôn
✅ "Còn bao nhiêu PLC RACER?"
✅ "Hóa đơn số 123"
✅ "Cách in hóa đơn"

❌ "Tab Sản phẩm làm gì?" → Không có quyền
❌ "Xem báo cáo doanh thu" → Không có quyền
```

### **👔 Accountant (Kế toán)**

```
✅ "Tổng doanh thu tháng này"
✅ "Báo cáo công đoạn"
✅ "Chênh lệch xuất bỏ"
✅ "Giao dịch sổ quỹ"
✅ "Danh sách sản phẩm"
✅ "Lịch sử giá PLC KOMAT"

❌ "Thêm user mới" → Chỉ Admin
```

### **👑 Admin**

```
✅ TẤT CẢ câu hỏi của Staff + Accountant
✅ "Danh sách user"
✅ "User nào là admin?"
✅ "Thêm sản phẩm mới"
✅ "Xóa user"
✅ "Cấu hình AI settings"
```

---

## 🛠️ 12. CONFIGURATION (Cài đặt)

### **File:** `ai/config.json`

```json
{
  "groq_api_key": "gsk_...",
  "ai_mode": "online",
  "model_name": "llama-3.3-70b-versatile",
  "max_history": 10,
  "cache_ttl": 300
}
```

### **Trong App:**

**Tab Cài đặt → AI Settings:**

- ✅ Nhập Groq API Key
- ✅ Test kết nối
- ✅ Switch Online/Offline
- ✅ Clear cache

---

## 📊 13. PERFORMANCE

### **Online Mode (Groq API):**

- **Tốc độ:** 1-2 giây
- **Độ chính xác:** 95%+
- **Context:** 8K tokens
- **Cost:** FREE (60 requests/minute)

### **Offline Mode (Phi3:mini):**

- **Tốc độ:** 5-10 giây
- **Độ chính xác:** 70-80%
- **Context:** 2K tokens
- **Cost:** FREE (local)

---

## 🔄 14. UPDATE HISTORY

| Ngày           | Cập nhật                                               |
| -------------- | ------------------------------------------------------ |
| **08/11/2024** | ✅ Điều chỉnh IT Security Filter - Cho phép query data |
| **07/11/2024** | ✅ Thêm splash screen animation                        |
| **06/11/2024** | ✅ Rename app → ShopFlow 2.5.0                         |
| **05/11/2024** | ✅ Split Settings tab → AI Settings + Information      |
| **04/11/2024** | ✅ Auto-stretch product name columns                   |
| **03/11/2024** | ✅ Permission system + IT Security Filter              |
| **02/11/2024** | ✅ Auto tab switching                                  |
| **01/11/2024** | ✅ Hybrid AI (Groq + Phi3)                             |

---

## 📞 SUPPORT

### **Câu hỏi thường gặp:**

**Q: AI không trả lời được câu hỏi?**  
A: Kiểm tra:

1. Groq API key (Tab Cài đặt → AI Settings)
2. Internet connection (nếu dùng Online mode)
3. Quyền user (Staff không xem được báo cáo)

**Q: AI trả lời sai?**  
A: Báo cáo trong `src/ai_offline_pro/wrong_answers.txt`, chạy `auto_trainer.py`

**Q: Muốn AI thông minh hơn?**  
A: Dùng Groq API (Online mode) thay vì Phi3 (Offline)

---

## 🎓 KẾT LUẬN

AI của ShopFlow có thể:

- ✅ Trả lời **TẤT CẢ** câu hỏi về sử dụng app
- ✅ **Truy vấn database** (READ-ONLY) an toàn
- ✅ **Tự động chuyển tab** khi trả lời
- ✅ **Nhớ ngữ cảnh** 10 Q&A gần nhất
- ✅ **Phân quyền** chặt chẽ theo role
- ✅ **Chặn thông tin IT** nhạy cảm
- ✅ **Học từ lỗi** tự động

AI **KHÔNG THỂ:**

- ❌ Sửa/xóa dữ liệu database
- ❌ Tiết lộ password, API key
- ❌ Cung cấp source code, cấu trúc DB
- ❌ Bypass quyền user

**→ An toàn, thông minh, hữu ích!** 🚀
