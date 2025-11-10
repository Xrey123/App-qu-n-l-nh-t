# 🎯 TÓM TẮT - TÍCH HỢP ZALO NOTIFICATION

## ✅ Files đã tạo

### 1. Core System

```
utils/zalo_notification.py          # Hệ thống gửi thông báo Zalo
├── ZaloNotifier                     # Zalo Official Account API
├── SimpleZaloNotifier               # Zalo Webhook (đơn giản)
└── Helper functions                 # notify_user_balance(), etc.
```

### 2. Database

```
users.py                             # Thêm functions:
├── lay_user_phone()                 # Lấy số phone của user
├── cap_nhat_user_phone()            # Cập nhật phone
└── lay_users_co_no()                # Lấy users đang nợ
```

### 3. Migration & Setup

```
migration_add_phone.py               # Thêm cột phone vào Users
update_user_phones.py                # Cập nhật phone cho users
test_zalo_notification.py            # Test hệ thống
.env.zalo.example                    # Example config
```

### 4. Documentation

```
HUONG_DAN_ZALO_NOTIFICATION.md      # Hướng dẫn chi tiết setup
```

---

## 🚀 SETUP NHANH (5 BƯỚC)

### Bước 1: Thêm cột phone vào DB

```bash
cd "d:\f app"
python migration_add_phone.py
```

### Bước 2: Cập nhật phone cho users

```bash
python update_user_phones.py
# Chọn option 1 (interactive) hoặc 2 (từ code)
```

### Bước 3: Đăng ký Zalo OA

1. Truy cập: https://oa.zalo.me/
2. Đăng ký Official Account
3. Tạo app tại: https://developers.zalo.me/
4. Lấy access_token và OA_ID

### Bước 4: Cấu hình .env

```bash
# Copy example file
copy .env.zalo.example .env

# Sửa file .env với thông tin thật
ZALO_ACCESS_TOKEN=your_token_here
ZALO_OA_ID=your_oa_id_here
```

### Bước 5: Test

```bash
python test_zalo_notification.py
```

---

## 💻 TÍCH HỢP VÀO APP

### Option 1: Nút gửi thông báo trong tab Sổ quỹ

Thêm vào `main_gui.py` - trong hàm `init_tab_so_quy()`:

```python
# Sau dòng: btn_chuyen_tien = QPushButton("Chuyển tiền")
btn_send_zalo = QPushButton("📱 Gửi thông báo Zalo")
btn_send_zalo.clicked.connect(self.send_zalo_notifications_click)
btn_layout_quy.addWidget(btn_send_zalo)

# Thêm function mới:
def send_zalo_notifications_click(self):
    """Gửi thông báo Zalo cho users đang nợ"""
    from utils.zalo_notification import ZaloNotifier
    from users import lay_users_co_no
    from PyQt5.QtWidgets import QMessageBox

    # Confirm
    reply = QMessageBox.question(
        self,
        "Xác nhận",
        "Gửi thông báo Zalo cho tất cả users đang nợ?",
        QMessageBox.Yes | QMessageBox.No
    )

    if reply != QMessageBox.Yes:
        return

    # Get users with debt
    users_with_debt = lay_users_co_no(threshold=-100000)

    if not users_with_debt:
        show_info(self, "Thông báo", "Không có user nào đang nợ")
        return

    # Send notifications
    notifier = ZaloNotifier()
    success_count = 0
    failed_count = 0

    for user_id, username, phone, so_du in users_with_debt:
        if not phone:
            logger.warning(f"User {username} không có phone")
            failed_count += 1
            continue

        success = notifier.send_balance_notification(
            user_phone=phone,
            username=username,
            balance=so_du
        )

        if success:
            success_count += 1
        else:
            failed_count += 1

    # Show result
    show_success(
        self,
        f"Đã gửi {success_count} thông báo\n"
        f"Thất bại: {failed_count}"
    )
```

### Option 2: Tự động gửi khi đóng ca có nợ

Thêm vào hàm `close_shift()` trong `dong_ca_in_pdf()`:

```python
def close_shift():
    # ... existing code ...

    # Sau khi đóng ca thành công
    if tong_thieu < 0:  # Nợ
        from utils.zalo_notification import notify_user_balance
        from users import lay_user_phone

        user_phone = lay_user_phone(self.user_id)
        if user_phone:
            notify_user_balance(
                user_id=self.user_id,
                username=current_user_name,
                balance=tong_thieu,
                phone=user_phone,
                method="oa"
            )
            logger.info(f"Sent Zalo notification to {current_user_name}")
```

### Option 3: Gửi định kỳ hàng ngày (9h sáng)

Thêm vào `__init__()` của `MainWindow`:

```python
def __init__(self, user_id, login_window=None):
    # ... existing code ...

    # ✨ Zalo notification timer
    from PyQt5.QtCore import QTimer

    def check_daily_notifications():
        from datetime import datetime
        now = datetime.now()

        if now.hour == 9 and now.minute == 0:  # 9h sáng
            from utils.zalo_notification import notify_all_negative_balances
            results = notify_all_negative_balances(threshold=-50000)
            logger.info(f"Daily Zalo: {results['success']} sent, {results['failed']} failed")

    self.notification_timer = QTimer()
    self.notification_timer.timeout.connect(check_daily_notifications)
    self.notification_timer.start(60000)  # Check every minute
```

---

## 📊 FEATURES

### ✅ Đã có:

- [x] Gửi thông báo số dư qua Zalo OA
- [x] Gửi thông báo qua Webhook (đơn giản)
- [x] Gửi cho 1 user
- [x] Gửi hàng loạt
- [x] Lọc users đang nợ
- [x] Logging đầy đủ
- [x] Error handling

### 💡 Có thể mở rộng:

- [ ] Gửi thông báo khi có hóa đơn mới
- [ ] Thông báo khi sản phẩm sắp hết
- [ ] Reminder tự động mỗi 3 ngày nếu chưa nộp
- [ ] Dashboard xem tỷ lệ mở tin nhắn
- [ ] Template tin nhắn có hình ảnh

---

## 🎨 CUSTOMIZE MESSAGE

Sửa trong `utils/zalo_notification.py`:

```python
def send_balance_notification(self, user_phone, username, balance):
    # Custom message theo ý bạn
    message = f"""
🏪 {YOUR_SHOP_NAME}

Xin chào {username} 👋

💰 Số dư hiện tại: {format_price(balance)} VNĐ

{"⚠️ VUI LÒNG NỘP TIỀN SỚM!" if balance < 0 else "✅ CẢM ƠN BẠN"}

📞 Hotline: {YOUR_PHONE}
🏪 Địa chỉ: {YOUR_ADDRESS}
    """
    return self._send_text_message(user_phone, message.strip())
```

---

## 🐛 TROUBLESHOOTING

### Lỗi: "Access token expired"

```
→ Lấy token mới từ https://developers.zalo.me/
→ Update .env file
```

### Lỗi: "User not found"

```
→ User chưa follow OA
→ Yêu cầu user follow OA trước khi gửi
```

### Lỗi: "Invalid phone number"

```
→ Phone phải format: 84xxxxxxxxx
→ Không có dấu +, không có số 0 đầu
→ VD: 84987654321 (đúng), 0987654321 (sai)
```

### Không nhận được tin nhắn

```
1. Check user đã follow OA chưa
2. Check access token còn hạn không
3. Check logs/shopflow_*.log
4. Test với phone khác
```

---

## 📝 CHECKLIST ĐẦY ĐỦ

### Database:

- [ ] Chạy migration_add_phone.py
- [ ] Cập nhật phone cho tất cả users
- [ ] Verify: SELECT id, username, phone FROM Users

### Zalo Setup:

- [ ] Đăng ký Zalo OA
- [ ] Tạo app developers.zalo.me
- [ ] Lấy access_token
- [ ] Lấy OA_ID
- [ ] Thêm vào .env file

### Users:

- [ ] Yêu cầu tất cả users follow OA
- [ ] Verify users xuất hiện trong follower list

### Testing:

- [ ] Chạy test_zalo_notification.py
- [ ] Gửi test message cho 1 user
- [ ] Verify user nhận được tin nhắn
- [ ] Check logs

### Integration:

- [ ] Thêm nút vào tab Sổ quỹ (optional)
- [ ] Thêm auto-send khi đóng ca (optional)
- [ ] Thêm daily reminder (optional)
- [ ] Test end-to-end

---

## 💰 CHI PHÍ DỰ KIẾN

### Zalo OA:

- Free: 1000 messages/tháng ✅
- Paid: 200đ/message
- Với ~10 users, ~30 notifications/tháng = **FREE** ✅

### Development:

- Setup time: 2-3 giờ
- Testing: 1 giờ
- Total: **3-4 giờ**

---

## 📞 HỖ TRỢ

- Zalo Developers: https://developers.zalo.me/docs/
- OA Support: https://oa.zalo.me/support
- Email: support@zalo.me

---

**Cập nhật:** 09/11/2025  
**Status:** ✅ Ready for integration
