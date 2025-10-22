# Quick script to run the same queries used by xem_bao_cao_kho and print results
import os
import sys

# Ensure project root is on sys.path so relative imports like 'db' work
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from db import ket_noi

conn = ket_noi()
c = conn.cursor()

c.execute("SELECT id, ten, ton_kho, gia_buon, nguong_buon FROM SanPham ORDER BY ten")
sps = c.fetchall()

print("product | ton_kho | sl_xhd | sl_xuat_bo | sl_chua_xuat | SYS")
for sp in sps:
    sp_id, ten, ton_kho, _, nguong_buon = sp
    c.execute(
        "SELECT COALESCE(SUM(so_luong), 0) FROM ChiTietHoaDon WHERE sanpham_id = ? AND xuat_hoa_don = 1",
        (sp_id,),
    )
    sl_xhd = c.fetchone()[0] or 0
    c.execute(
        "SELECT COALESCE(SUM(so_luong), 0) FROM LogKho WHERE sanpham_id = ? AND hanh_dong = 'xuat'",
        (sp_id,),
    )
    sl_xuat_bo = c.fetchone()[0] or 0
    c.execute(
        "SELECT COALESCE(SUM(so_luong), 0) FROM ChiTietHoaDon WHERE sanpham_id = ? AND xuat_hoa_don = 0",
        (sp_id,),
    )
    sl_chua_xuat = c.fetchone()[0] or 0
    sys_val = (ton_kho or 0) + (sl_chua_xuat or 0)
    print(f"{ten} | {ton_kho} | {sl_xhd} | {sl_xuat_bo} | {sl_chua_xuat} | {sys_val}")

conn.close()
