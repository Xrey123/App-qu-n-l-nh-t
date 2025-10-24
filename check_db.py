"""
Kiểm tra database trực tiếp
"""
import sqlite3
from db import DB_NAME

print(f"Đang kết nối tới database: {DB_NAME}")
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

print("=== BẢNG DauKyXuatBo ===")
c.execute("SELECT COUNT(*) FROM DauKyXuatBo")
print(f"Tổng số record: {c.fetchone()[0]}")

c.execute("""
    SELECT s.ten, dk.loai_gia, dk.so_luong
    FROM DauKyXuatBo dk
    JOIN SanPham s ON dk.sanpham_id = s.id
    LIMIT 10
""")
for row in c.fetchall():
    print(f"  {row[0]} - {row[1]}: {row[2]}")

print("\n=== BẢNG LogKho (xuat_bo) ===")
c.execute("SELECT COUNT(*) FROM LogKho WHERE hanh_dong = 'xuat_bo'")
print(f"Tổng số record xuất: {c.fetchone()[0]}")

c.execute("""
    SELECT s.ten, lk.loai_gia, lk.so_luong
    FROM LogKho lk
    JOIN SanPham s ON lk.sanpham_id = s.id
    WHERE lk.hanh_dong = 'xuat_bo'
    LIMIT 10
""")
print("Các lần xuất gần đây:")
for row in c.fetchall():
    print(f"  {row[0]} - {row[1]}: {row[2]}")

conn.close()
print("\n✓ Hoàn thành")
