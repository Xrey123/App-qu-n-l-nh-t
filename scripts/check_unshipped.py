import sqlite3

conn = sqlite3.connect("fapp.db")
c = conn.cursor()
c.execute(
    "SELECT s.id, s.ten, COALESCE(SUM(c.so_luong),0) as sl_chua_xuat FROM SanPham s LEFT JOIN ChiTietHoaDon c ON s.id=c.sanpham_id AND c.xuat_hoa_don=0 GROUP BY s.id, s.ten ORDER BY s.ten LIMIT 100"
)
rows = c.fetchall()
print("product_id | ten | sl_chua_xuat")
for r in rows:
    print(r)
conn.close()
