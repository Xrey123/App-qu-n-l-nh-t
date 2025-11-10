# 🧪 TEST AUTO TAB SWITCHING

**Ngày test:** 09/11/2024
**Phiên bản:** 2.5.0
**Các file đã sửa:**
- `ai_system/hybrid.py` - Sửa hàm `_auto_switch_tab()`
- `main_gui.py` - Cải thiện hàm `navigate_to_tab()`
- `ai/app_knowledge_enhanced.json` - Cập nhật thông tin tabs

---

## ✅ CHECKLIST TEST

### **1. Test Tab Cơ Bản**
Hãy hỏi AI các câu sau và kiểm tra xem có tự động chuyển tab đúng không:

- [ ] **"tab sản phẩm"** → Phải chuyển đến tab "Sản phẩm"
- [ ] **"hướng dẫn xuất hóa đơn"** → Phải chuyển đến tab "Hóa đơn"
- [ ] **"cài đặt groq api"** → Phải chuyển đến tab "⚙️ Cài đặt"
- [ ] **"tab báo cáo"** → Phải chuyển đến tab "Báo cáo"
- [ ] **"quản lý user"** → Phải chuyển đến tab "Quản lý User" (Admin only)

---

### **2. Test Sub-Tabs (Quan Trọng!)**

#### **Tab "Ca bán hàng":**
- [ ] **"hướng dẫn nhận hàng"** → Phải chuyển đến **Ca bán hàng > Nhận hàng** (sub-tab 0)
- [ ] **"cách kiểm kê kho"** → Phải chuyển đến **Ca bán hàng > Nhận hàng**
- [ ] **"hướng dẫn bán hàng"** → Phải chuyển đến **Ca bán hàng > Bán hàng** (sub-tab 1)
- [ ] **"thanh toán đơn hàng"** → Phải chuyển đến **Ca bán hàng > Bán hàng**

---

### **3. Test "Chi tiết bán" (Dễ Nhầm!)**

**MỤC ĐÍCH:** Đảm bảo AI không nhầm giữa "bán hàng" và "chi tiết bán"

- [ ] **"xem sản phẩm đã bán"** → Phải chuyển đến **Chi tiết bán** (KHÔNG phải "Bán hàng")
- [ ] **"danh sách hàng đã bán"** → Phải chuyển đến **Chi tiết bán**
- [ ] **"làm thế nào xem đã bán gì?"** → Phải chuyển đến **Chi tiết bán**
- [ ] **"tab chi tiết bán làm gì?"** → Phải chuyển đến **Chi tiết bán**
- [ ] **"nộp tiền cho accountant"** → Phải chuyển đến **Chi tiết bán**

---

### **4. Test Tabs Cho Accountant/Admin**

#### **Tab "Xuất bổ":**
- [ ] **"hướng dẫn xuất bổ"** → Phải chuyển đến **Xuất bổ** (Accountant only)
- [ ] **"tab xuất bỏ làm gì?"** → Phải chuyển đến **Xuất bổ**

#### **Tab "Công đoàn":**
- [ ] **"chuyển tiền công đoàn"** → Phải chuyển đến **Công đoàn** (Admin only)
- [ ] **"tab công đoàn"** → Phải chuyển đến **Công đoàn**
- [ ] **"quỹ công đoàn"** → Phải chuyển đến **Công đoàn**

#### **Tab "Sổ quỹ":**
- [ ] **"xem lịch sử giao dịch"** → Phải chuyển đến **Sổ quỹ**
- [ ] **"tab sổ quỹ"** → Phải chuyển đến **Sổ quỹ**

#### **Tab "Chênh lệch":**
- [ ] **"xử lý chênh lệch kho"** → Phải chuyển đến **Chênh lệch**
- [ ] **"tab chênh lệch"** → Phải chuyển đến **Chênh lệch**

---

### **5. Test Permissions (Phân Quyền)**

**Login với Staff user và test:**

- [ ] **"tab sản phẩm"** → AI phải TỪ CHỐI và nói chỉ dành cho Admin/Accountant
- [ ] **"xuất bổ"** → AI phải TỪ CHỐI
- [ ] **"công đoàn"** → AI phải TỪ CHỐI
- [ ] **"sổ quỹ"** → AI phải TỪ CHỐI

**Nhưng Staff CÓ THỂ truy cập:**
- [ ] **"tab chi tiết bán"** → Phải chuyển thành công
- [ ] **"hóa đơn"** → Phải chuyển thành công
- [ ] **"nhận hàng"** → Phải chuyển thành công
- [ ] **"bán hàng"** → Phải chuyển thành công

---

### **6. Test AI Trả Lời + Tự Động Chuyển Tab**

Các câu hỏi này AI phải vừa TRẢ LỜI vừa TỰ ĐỘNG CHUYỂN TAB:

- [ ] **"liệt kê tất cả 13 tabs trong app"**
  - AI trả lời: Liệt kê đầy đủ 14 tabs
  - Tự động chuyển: KHÔNG (vì không hỏi về tab cụ thể)

- [ ] **"trong tab chi tiết bán, làm thế nào xem sản phẩm đã bán?"**
  - AI trả lời: Hướng dẫn click nút "Chi tiết"
  - Tự động chuyển: Đến tab "Chi tiết bán" ✅

- [ ] **"tab công đoàn có nút chuyển tiền, nó làm gì?"**
  - AI trả lời: Giải thích chức năng nút chuyển tiền
  - Tự động chuyển: Đến tab "Công đoàn" ✅

- [ ] **"cách tính giá buôn trong app"**
  - AI trả lời: Giải thích logic tính giá
  - Tự động chuyển: KHÔNG (vì không hỏi về tab cụ thể)

---

## 📊 KẾT QUẢ TEST

**Tổng số test cases:** 35+

**Đã pass:** _____ / 35

**Failed:** _____

**Lỗi phát hiện:**
1. _____________________________________
2. _____________________________________
3. _____________________________________

---

## 🐛 BUGS ĐÃ PHÁT HIỆN

### **Bug 1: [Mô tả ngắn]**
- **Tái hiện:** _____________________________________
- **Expected:** _____________________________________
- **Actual:** _____________________________________
- **Fix:** _____________________________________

---

## 📝 GHI CHÚ

- App đã chạy thành công, không có lỗi Python
- Cần test thủ công vì PyQt5 GUI không thể test tự động dễ dàng
- Đảm bảo đã bật Groq API để AI thông minh hơn

---

## ✅ APPROVAL

- [ ] Tất cả test cases đều PASS
- [ ] AI trả lời chính xác về tabs
- [ ] Tự động chuyển tab hoạt động đúng
- [ ] Không có lỗi runtime

**Người test:** _____________________  
**Ngày:** _____________________  
**Kết luận:** _____________________
