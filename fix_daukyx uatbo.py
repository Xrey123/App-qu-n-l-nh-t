"""
Script để xóa và tạo lại bảng DauKyXuatBo với schema đúng
"""

from db import ket_noi

conn = ket_noi()
c = conn.cursor()

# Xóa bảng cũ
print("Đang xóa bảng DauKyXuatBo cũ...")
c.execute("DROP TABLE IF EXISTS DauKyXuatBo")

# Tạo lại với schema đúng
print("Đang tạo lại bảng DauKyXuatBo với schema mới...")
c.execute(
    """
    CREATE TABLE DauKyXuatBo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        sanpham_id INTEGER,
        ten_sanpham TEXT,
        so_luong REAL,
        loai_gia TEXT,
        gia REAL,
        ngay TEXT,
        FOREIGN KEY(user_id) REFERENCES Users(id),
        FOREIGN KEY(sanpham_id) REFERENCES SanPham(id)
    )
"""
)

conn.commit()
conn.close()

print("✓ Hoàn thành! Bảng DauKyXuatBo đã được tạo lại với schema đúng.")
print("Bây giờ bạn cần vào tab 'Nhập đầu kỳ' và nhập lại dữ liệu sản phẩm.")
