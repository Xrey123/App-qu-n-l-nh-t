# 📱 HƯỚNG DẪN TÍCH HỢP ZALO NOTIFICATION

## 🎯 MỤC ĐÍCH
Gửi thông báo số dư nợ qua Zalo cho nhân viên khi:
- Đóng ca có số dư âm (nợ)
- Kiểm tra định kỳ (hàng ngày)
- Accountant muốn nhắc nhở

---

## 🚀 CÁCH 1: ZALO OFFICIAL ACCOUNT (Chuyên nghiệp) ⭐⭐⭐

### Bước 1: Đăng ký Zalo OA

1. **Truy cập:** https://oa.zalo.me/
2. **Đăng ký** Official Account cho shop
3. **Xác thực** (cần GPKD nếu doanh nghiệp)

### Bước 2: Tạo App Developer

1. **Truy cập:** https://developers.zalo.me/
2. **Tạo app mới** → Chọn "Official Account API"
3. **Lấy thông tin:**
   - App ID
   - App Secret
   - OA ID

### Bước 3: Lấy Access Token

```bash
# Method 1: Qua OAuth (recommended)
https://oauth.zaloapp.com/v3/permission?app_id={APP_ID}&redirect_uri={REDIRECT_URI}&state={STATE}

# Method 2: Qua Dashboard
https://developers.zalo.me/apps/{APP_ID}/settings
```

### Bước 4: Thêm Users vào OA

Nhân viên cần:
1. Cài Zalo app
2. Follow Official Account của shop
3. Admin lấy `user_id` từ follower list

### Bước 5: Cấu hình .env

```bash
# Tạo/Sửa file .env trong d:\f app\
ZALO_ACCESS_TOKEN=your_access_token_here
ZALO_OA_ID=your_oa_id_here
```

### Bước 6: Thêm cột phone vào Users

```sql
-- Chạy trong SQLite
ALTER TABLE Users ADD COLUMN phone TEXT;

-- Cập nhật phone cho users
UPDATE Users SET phone = '84987654321' WHERE username = 'user1';
UPDATE Users SET phone = '84912345678' WHERE username = 'user2';
```

### Bước 7: Test gửi thông báo

```python
# test_zalo_notification.py
from utils.zalo_notification import ZaloNotifier

notifier = ZaloNotifier()

# Test gửi cho 1 user
success = notifier.send_balance_notification(
    user_phone="84987654321",  # Số phone thật của nhân viên
    username="Nguyễn Văn A",
    balance=-500000,  # Nợ 500k
    balance_type="nợ"
)

if success:
    print("✅ Gửi thành công!")
else:
    print("❌ Gửi thất bại! Check log.")
```

---

## 🔧 CÁCH 2: ZALO WEBHOOK (Đơn giản hơn) ⭐⭐

### Ưu điểm:
- Không cần đăng ký OA
- Setup nhanh
- Free

### Nhược điểm:
- Message gửi vào group (công khai)
- Không gửi riêng tư từng người

### Bước 1: Tạo Zalo Group

1. Tạo group Zalo với tất cả nhân viên
2. Thêm bot vào group (hoặc dùng Zapier/Make.com)

### Bước 2: Tạo Webhook

**Option A: Dùng Make.com (khuyên dùng)**
1. Đăng ký: https://www.make.com/
2. Tạo scenario: Webhook → Zalo
3. Copy webhook URL

**Option B: Dùng Zapier**
1. Đăng ký: https://zapier.com/
2. Tạo Zap: Webhooks → Zalo
3. Copy webhook URL

### Bước 3: Cấu hình .env

```bash
ZALO_WEBHOOK_URL=https://hook.us1.make.com/xxxxxxxx
```

### Bước 4: Test

```python
from utils.zalo_notification import SimpleZaloNotifier

notifier = SimpleZaloNotifier()
notifier.send_balance_notification(
    username="Nguyễn Văn A",
    balance=-500000
)
```

---

## 💻 TÍCH HỢP VÀO MAIN_GUI.PY

### 1. Gửi thông báo khi đóng ca

```python
# Trong hàm dong_ca_in_pdf() - Line ~7500
def close_shift():
    # ... existing code ...
    
    # ✨ GỬI THÔNG BÁO ZALO NẾU NỢ
    if tong_thieu < 0:  # Nợ
        from utils.zalo_notification import notify_user_balance
        from users import lay_user_phone  # Cần tạo hàm này
        
        user_phone = lay_user_phone(self.user_id)
        if user_phone:
            notify_user_balance(
                user_id=self.user_id,
                username=current_user_name,
                balance=tong_thieu,
                phone=user_phone,
                method="oa"  # hoặc "webhook"
            )
            logger.info(f"Sent Zalo notification to {current_user_name}")
```

### 2. Nút "Gửi thông báo Zalo" trong tab Sổ quỹ

```python
# Trong init_tab_so_quy() - Line ~6879
def init_tab_so_quy(self):
    # ... existing code ...
    
    # Nút gửi thông báo Zalo
    btn_send_zalo = QPushButton("📱 Gửi thông báo Zalo")
    btn_send_zalo.clicked.connect(self.send_zalo_notifications)
    btn_layout_quy.addWidget(btn_send_zalo)
    
    # ... rest of code ...

def send_zalo_notifications(self):
    """Gửi thông báo số dư cho users đang nợ"""
    from utils.zalo_notification import notify_all_negative_balances
    from PyQt5.QtWidgets import QMessageBox
    
    reply = QMessageBox.question(
        self,
        "Xác nhận",
        "Gửi thông báo Zalo cho tất cả users đang nợ?",
        QMessageBox.Yes | QMessageBox.No
    )
    
    if reply == QMessageBox.Yes:
        results = notify_all_negative_balances(threshold=-100000)
        
        show_success(
            self,
            f"Đã gửi {results['success']} thông báo\n"
            f"Thất bại: {results['failed']}"
        )
```

### 3. Gửi tự động hàng ngày (Optional)

```python
# Trong __init__() của MainWindow - Line ~400
def __init__(self, user_id, login_window=None):
    # ... existing code ...
    
    # Timer gửi thông báo hàng ngày lúc 9h sáng
    from PyQt5.QtCore import QTimer
    from datetime import datetime
    
    def check_and_send_notifications():
        now = datetime.now()
        if now.hour == 9 and now.minute == 0:  # 9h sáng
            from utils.zalo_notification import notify_all_negative_balances
            notify_all_negative_balances(threshold=-50000)
            logger.info("Sent daily Zalo notifications")
    
    # Check mỗi phút
    self.notification_timer = QTimer()
    self.notification_timer.timeout.connect(check_and_send_notifications)
    self.notification_timer.start(60000)  # 60 seconds
```

---

## 📊 TEST VÀ DEBUG

### Test basic

```bash
cd "d:\f app"
python test_zalo_notification.py
```

### Xem log

```bash
notepad logs\shopflow_20251109.log
```

### Các lỗi thường gặp

**1. Access token expired**
```
Error: Invalid access token
Fix: Lấy token mới từ https://developers.zalo.me/
```

**2. User not following OA**
```
Error: User not found
Fix: User cần follow OA trước
```

**3. Phone number format sai**
```
Error: Invalid phone number
Fix: Dùng format 84xxxxxxxxx (không có +, không có 0 đầu)
```

---

## 🎨 CUSTOMIZE MESSAGE

Sửa trong `utils/zalo_notification.py`:

```python
def send_balance_notification(self, user_phone, username, balance):
    # Custom message
    message = f"""
🏪 SHOPFLOW - THÔNG BÁO SỐ DƯ

👤 Nhân viên: {username}
💰 Số dư hiện tại: {format_price(balance)} VNĐ

{"⚠️ BẠN ĐANG NỢ!" if balance < 0 else "✅ ĐÃ THANH TOÁN"}

📞 Liên hệ kế toán nếu có thắc mắc
    """
    
    return self._send_text_message(user_phone, message.strip())
```

---

## 💰 CHI PHÍ

### Zalo OA:
- **Free tier:** 1000 messages/tháng
- **Paid:** 200đ/message
- **Enterprise:** Liên hệ Zalo

### Webhook (Make.com):
- **Free:** 1000 operations/tháng
- **Paid:** $9/tháng (10,000 ops)

---

## 📝 CHECKLIST SETUP

- [ ] Đăng ký Zalo OA
- [ ] Tạo app tại developers.zalo.me
- [ ] Lấy access_token và OA_ID
- [ ] Thêm vào file .env
- [ ] Thêm cột phone vào bảng Users
- [ ] Cập nhật phone cho tất cả users
- [ ] Users follow OA
- [ ] Test gửi thông báo
- [ ] Tích hợp vào main_gui.py
- [ ] Test end-to-end

---

## 🆘 HỖ TRỢ

- **Zalo Developers:** https://developers.zalo.me/docs/
- **OA Support:** https://oa.zalo.me/support
- **Community:** https://github.com/zaloplatform

---

**Cập nhật:** 09/11/2025  
**Tác giả:** AI Assistant
