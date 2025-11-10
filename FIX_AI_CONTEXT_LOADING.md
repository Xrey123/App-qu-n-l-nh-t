# FIX: AI Context Loading Issue

## 🐛 Vấn đề (Problem)

AI trả lời sai số lượng tabs trong app (nói 7 tabs thay vì 14 tabs) mặc dù `app_knowledge_enhanced.json` đã có đầy đủ thông tin.

**Ví dụ lỗi:**
- User hỏi: "có tổng bao nhiêu tab tôi cần học trong app"
- AI trả lời: "có 7 tab chính" ❌ SAI
- Thực tế: App có 14 tabs ✅ ĐÚNG

## 🔍 Nguyên nhân (Root Cause)

File `ai_system/hybrid.py` có hàm `_build_context()` **HARDCODE** danh sách tabs thay vì đọc từ JSON:

```python
# CÁCH CŨ - HARDCODE (SAI) ❌
context = f"""
📊 CHỨC NĂNG CHÍNH:
- 🏠 Trang chủ: Dashboard, thống kê
- 📦 Sản phẩm: Quản lý danh sách nhớt (Admin/Accountant)
- 🛒 Ca bán hàng: Nhận hàng (kiểm kê) + Bán hàng
- 📄 Hóa đơn: Xuất hóa đơn, in PDF
- 👥 Khách hàng: Quản lý khách, check VIP
- 📊 Báo cáo: Doanh thu, lợi nhuận, tổng kết ca
- ⚙️ Cài đặt: Groq API (online AI mode)
"""
```

**Vấn đề:** Danh sách hardcode này chỉ có 7 tabs, trong khi app thực tế có 14 tabs!

## ✅ Giải pháp (Solution)

### 1. Sửa `ai_system/hybrid.py` - Đọc động từ JSON

```python
# CÁCH MỚI - DYNAMIC LOADING (ĐÚNG) ✅
def _build_context(self) -> str:
    app_info = self.app_knowledge.get("app_info", {})
    
    # Đọc động từ JSON
    total_tabs = app_info.get('tổng_số_tabs', 14)
    tabs_list = app_info.get('danh_sách_tabs', [])
    important_note = app_info.get('lưu_ý_quan_trọng', '')
    
    # Build tabs string từ JSON
    tabs_string = '\n'.join(tabs_list) if tabs_list else "..."
    
    context = f"""
📊 DANH SÁCH {total_tabs} TABS TRONG APP:
{tabs_string}

⚠️ LƯU Ý QUAN TRỌNG:
{important_note}
"""
```

### 2. Sửa `ai/app_knowledge_enhanced.json` - Đúng số lượng

**Trước (SAI):**
```json
{
  "app_info": {
    "tổng_số_tabs": 13,  ❌ SAI (list có 14 items)
    "danh_sách_13_tabs": [...]
  }
}
```

**Sau (ĐÚNG):**
```json
{
  "app_info": {
    "tổng_số_tabs": 14,  ✅ ĐÚNG
    "danh_sách_tabs": [
      "1. 🏠 Trang chủ - Dashboard, thống kê tổng quan",
      "2. Sản phẩm - Quản lý danh sách nhớt",
      "3. Lịch sử giá - Xem lịch sử thay đổi giá",
      "4. Ca bán hàng - 2 sub-tabs: Nhận hàng + Bán hàng",
      "5. Chi tiết bán - XEM SẢN PHẨM ĐÃ BÁN",
      "6. Hóa đơn - Quản lý hóa đơn đã xuất",
      "7. Báo cáo - Báo cáo kho, biểu đồ sản lượng",
      "8. Quản lý User - Quản lý tài khoản user",
      "9. Chênh lệch - Xử lý chênh lệch kho",
      "10. Xuất bổ - Xuất hàng bổ sung 3 loại giá",
      "11. Công đoàn - Quỹ công đoàn, 2 sub-tabs",
      "12. Sổ quỹ - Lịch sử thu chi tiền",
      "13. Nhập đầu kỳ - Nhập tồn kho ban đầu",
      "14. ⚙️ Cài đặt - Cấu hình Groq API"
    ]
  }
}
```

## 📋 Files Changed

1. **`ai_system/hybrid.py`** (lines 201-260)
   - Sửa hàm `_build_context()` để đọc động từ JSON
   - Thêm biến `total_tabs`, `tabs_list`, `important_note`

2. **`ai/app_knowledge_enhanced.json`** (lines 8-9)
   - Sửa `"tổng_số_tabs": 13` → `14`
   - Đổi tên `"danh_sách_13_tabs"` → `"danh_sách_tabs"`

## 🧪 Test

```python
import json

# Validate JSON
with open('ai/app_knowledge_enhanced.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    
print(f"Tổng số tabs: {data['app_info']['tổng_số_tabs']}")
print(f"Số lượng trong danh sách: {len(data['app_info']['danh_sách_tabs'])}")
# Output: 
# Tổng số tabs: 14
# Số lượng trong danh sách: 14
```

## 🎯 Kết quả (Result)

✅ AI bây giờ sẽ trả lời **ĐÚNG** khi được hỏi về số lượng tabs!

**Test câu hỏi:**
- ❓ "có tổng bao nhiêu tab tôi cần học trong app"
- ✅ AI sẽ trả lời: "Có 14 tabs trong app..." (ĐÚNG!)

## 📝 Lưu ý quan trọng

⚠️ **Mỗi khi update thông tin tabs trong `app_knowledge_enhanced.json`, AI sẽ TỰ ĐỘNG load thông tin mới!**

Không cần sửa code Python nữa, chỉ cần:
1. Sửa JSON file
2. Restart app
3. AI sẽ có kiến thức mới! 🚀

---

**Ngày sửa:** 2025-11-10  
**Người sửa:** GitHub Copilot  
**Issue:** AI trả lời sai số lượng tabs vì hardcode trong `_build_context()`
