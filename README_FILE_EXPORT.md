# Quản lý File Export

## Cấu trúc thư mục

Ứng dụng tự động tạo và quản lý các thư mục sau:

```
d:\f app\
├── data_export/              # Thư mục chính chứa tất cả file export
│   ├── nhan_hang/           # File CSV kiểm kê/nhận hàng
│   │   └── nhan_hang_[user_id]_[ngày giờ].csv
│   └── tong_ket_ca/         # File HTML tổng kết ca
│       └── tong_ket_ca_[user_id]_[ngày giờ].html
```

## Tính năng tự động

### 1. Tự động tạo thư mục
- Khi chạy ứng dụng, hệ thống tự động tạo thư mục `data_export/` nếu chưa tồn tại
- Tạo 2 thư mục con: `nhan_hang/` và `tong_ket_ca/`

### 2. Lưu file nhận hàng
- **Vị trí:** `data_export/nhan_hang/`
- **Định dạng:** `nhan_hang_[user_id]_[YYYYMMDD_HHMMSS].csv`
- **Khi nào:** Mỗi khi xác nhận nhận hàng
- **Nội dung:** Danh sách sản phẩm kiểm kê, số lượng đếm, tồn DB, chênh lệch, ghi chú

### 3. Lưu file tổng kết ca
- **Vị trí:** `data_export/tong_ket_ca/`
- **Định dạng:** `tong_ket_ca_[user_id]_[YYYYMMDD_HHMMSS].html`
- **Khi nào:** 
  - Khi in báo cáo đóng ca
  - Khi đóng ca (có hoặc không in)
- **Nội dung:** Báo cáo HTML đầy đủ về nhận hàng, bán hàng, chênh lệch, tài chính

### 4. Tự động xóa file cũ
- **Thời gian:** Xóa file cũ hơn **3 tháng** (90 ngày)
- **Khi nào:** 
  - Mỗi lần lưu file nhận hàng mới
  - Mỗi lần lưu file tổng kết ca mới
- **Mục đích:** Giảm dung lượng ổ đĩa, tránh lưu trữ quá nhiều file

## Lợi ích

✅ **Tổ chức tốt hơn:** Tất cả file export ở một nơi, dễ tìm kiếm và quản lý

✅ **Tự động hóa:** Không cần tạo thư mục thủ công

✅ **Tiết kiệm dung lượng:** Tự động xóa file cũ không còn cần thiết

✅ **An toàn dữ liệu:** File quan trọng được lưu trữ có tổ chức

✅ **Dễ backup:** Chỉ cần backup thư mục `data_export/`

## Lưu ý

- File cũ hơn 3 tháng sẽ **tự động bị xóa** khi có file mới được tạo
- Nếu muốn giữ file lâu hơn, hãy copy ra ngoài thư mục `data_export/`
- Thời gian 3 tháng có thể thay đổi trong code (tham số `so_thang` trong hàm `xoa_file_cu()`)

## Thay đổi thời gian xóa file

Nếu muốn thay đổi thời gian lưu trữ file (mặc định là 3 tháng), tìm và sửa trong file `main_gui.py`:

```python
# Trong hàm xac_nhan_nhan_hang()
xoa_file_cu(nhan_hang_dir, so_thang=3)  # Đổi số 3 thành số tháng mong muốn

# Trong hàm dong_ca_in_pdf()
xoa_file_cu(tong_ket_dir, so_thang=3)  # Đổi số 3 thành số tháng mong muốn
```

Ví dụ: Muốn lưu 6 tháng → đổi `so_thang=3` thành `so_thang=6`
