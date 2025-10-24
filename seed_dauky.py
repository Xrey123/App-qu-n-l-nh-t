from db import ket_noi
from products import tim_sanpham
from datetime import datetime

TEN = "PLC RACER 2T 1 lít"

conn = ket_noi()
c = conn.cursor()

sp = tim_sanpham(TEN)
if not sp:
    print(f"Không tìm thấy sản phẩm: {TEN}. Vui lòng tạo sản phẩm này trước.")
    conn.close()
    raise SystemExit(1)

sp_id = sp[0][0]
ngay = datetime.now().isoformat()

# Xóa dữ liệu cũ cho dễ test
c.execute("DELETE FROM DauKyXuatBo WHERE ten_sanpham = ?", (TEN,))

# Thêm mẫu: buôn 14, lẻ 10, vip 5
rows = [
    (sp_id, TEN, 14.0, "buon", sp[0][3], ngay),
    (sp_id, TEN, 10.0, "le", sp[0][2], ngay),
    (sp_id, TEN, 5.0, "vip", sp[0][4], ngay),
]
for sanpham_id, ten, so_luong, loai_gia, gia, ngay in rows:
    c.execute(
        """
        INSERT INTO DauKyXuatBo (user_id, sanpham_id, ten_sanpham, so_luong, loai_gia, gia, ngay)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (1, sanpham_id, ten, so_luong, loai_gia, gia, ngay),
    )

conn.commit()
conn.close()
print("✓ Đã seed DauKyXuatBo: buôn=14, lẻ=10, vip=5 cho:", TEN)
