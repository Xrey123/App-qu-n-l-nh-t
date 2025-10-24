"""
Test script để kiểm tra logic xuất bỏ
"""

from db import ket_noi


def kiem_tra_dau_ky():
    """Kiểm tra dữ liệu trong bảng DauKyXuatBo"""
    conn = ket_noi()
    c = conn.cursor()

    # Lấy tất cả dữ liệu đầu kỳ
    c.execute(
        """
        SELECT dk.id, s.ten, dk.loai_gia, dk.so_luong
        FROM DauKyXuatBo dk
        JOIN SanPham s ON dk.sanpham_id = s.id
        ORDER BY s.ten, dk.loai_gia
    """
    )

    print("=== DỮ LIỆU ĐẦU KỲ XUẤT BỎ ===")
    rows = c.fetchall()
    for row in rows:
        print(f"ID: {row[0]}, Tên: {row[1]}, Loại giá: {row[2]}, Số lượng: {row[3]}")

    # Tính tổng số lượng theo sản phẩm và loại giá
    c.execute(
        """
        SELECT s.ten, dk.loai_gia, SUM(dk.so_luong) as tong
        FROM DauKyXuatBo dk
        JOIN SanPham s ON dk.sanpham_id = s.id
        GROUP BY s.ten, dk.loai_gia
        ORDER BY s.ten, dk.loai_gia
    """
    )

    print("\n=== TỔNG THEO SẢN PHẨM VÀ LOẠI GIÁ ===")
    tong_sp = {}
    for row in c.fetchall():
        ten, loai_gia, tong = row
        print(f"{ten} - {loai_gia}: {tong}")
        tong_sp[(ten, loai_gia)] = tong

    # Trừ đi số lượng đã xuất
    c.execute(
        """
        SELECT s.ten, lk.loai_gia, SUM(lk.so_luong) as tong_xuat
        FROM LogKho lk
        JOIN SanPham s ON lk.sanpham_id = s.id
        WHERE lk.hanh_dong = 'xuat_bo'
        GROUP BY s.ten, lk.loai_gia
    """
    )

    print("\n=== ĐÃ XUẤT ===")
    da_xuat = {}
    for row in c.fetchall():
        ten, loai_gia, tong_xuat = row
        print(f"{ten} - {loai_gia}: {tong_xuat}")
        da_xuat[(ten, loai_gia)] = abs(tong_xuat)  # Chuyển về số dương

    # Tính còn lại
    print("\n=== CÒN LẠI ===")
    for (ten, loai_gia), so_luong in tong_sp.items():
        xuat = da_xuat.get((ten, loai_gia), 0)
        con_lai = so_luong - xuat
        print(f"{ten} - {loai_gia}: {so_luong} - {xuat} = {con_lai}")

    conn.close()
    return tong_sp, da_xuat


def test_xuat_buon(ten_sp, sl_xuat):
    """Test logic xuất buôn"""
    tong_sp, da_xuat = kiem_tra_dau_ky()

    print(f"\n=== TEST XUẤT BUÔN: {ten_sp}, SL: {sl_xuat} ===")

    # Tính số lượng còn lại cho từng loại giá
    sl_buon = tong_sp.get((ten_sp, "buon"), 0) - da_xuat.get((ten_sp, "buon"), 0)
    sl_le = tong_sp.get((ten_sp, "le"), 0) - da_xuat.get((ten_sp, "le"), 0)
    sl_vip = tong_sp.get((ten_sp, "vip"), 0) - da_xuat.get((ten_sp, "vip"), 0)

    print(f"Buôn có: {sl_buon}")
    print(f"Lẻ có: {sl_le}")
    print(f"VIP có: {sl_vip}")

    if sl_buon >= sl_xuat:
        print(f"✓ Đủ số lượng buôn để xuất {sl_xuat}")
    else:
        thieu = sl_xuat - sl_buon
        print(f"✗ Thiếu {thieu}, cần lấy từ lẻ")
        if sl_le >= thieu:
            print(f"✓ Lẻ có đủ {sl_le} để bù {thieu}")
        else:
            print(f"✗ Lẻ không đủ (có {sl_le}, cần {thieu})")


if __name__ == "__main__":
    kiem_tra_dau_ky()

    # Test với một sản phẩm cụ thể
    print("\n" + "=" * 60)
    test_xuat_buon("PLC RACER 2T 1 lít", 20)
