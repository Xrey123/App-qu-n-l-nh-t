import sqlite3
from datetime import datetime
from db import ket_noi
from stock import cap_nhat_kho_sau_ban
import pandas as pd


def tao_hoa_don(user_id, khach_hang, items, uu_dai, xuat_hoa_don, giam_gia):
    try:
        conn = ket_noi()
        c = conn.cursor()

        # Kiểm tra dữ liệu items
        for item in items:
            if "gia" not in item or not isinstance(item["gia"], (int, float)):
                print(f"Invalid gia for item {item}: gia must be a number")
                return (
                    False,
                    f"Giá không hợp lệ cho sản phẩm ID {item.get('sanpham_id', 'unknown')}",
                    None,
                )

        # ✅ KIỂM TRA TỒN KHO TRƯỚC KHI TẠO HÓA ĐƠN
        errors = []
        for item in items:
            sanpham_id = item["sanpham_id"]
            so_luong = item["so_luong"]

            # Lấy thông tin sản phẩm
            c.execute("SELECT ten, ton_kho FROM SanPham WHERE id = ?", (sanpham_id,))
            result = c.fetchone()
            if not result:
                errors.append(f"Sản phẩm ID {sanpham_id} không tồn tại")
                continue

            ten_sp, ton_kho = result

            # Kiểm tra tồn kho
            if ton_kho < so_luong:
                errors.append(
                    f"Sản phẩm '{ten_sp}' không đủ số lượng!\n"
                    f"  - Tồn kho: {ton_kho}\n"
                    f"  - Yêu cầu: {so_luong}\n"
                    f"  - Thiếu: {so_luong - ton_kho}"
                )

        # Nếu có lỗi tồn kho, KHÔNG tạo hóa đơn
        if errors:
            conn.close()
            return False, "\n\n".join(errors), None

        # Thêm hóa đơn vào bảng HoaDon
        ngay = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # trang_thai: Chua_xuat nếu có bất kỳ item nào XHĐ=0 (chưa xuất, cần xuất bổ sau)
        trang_thai = (
            "Chua_xuat"
            if any(item["xuat_hoa_don"] == 0 for item in items)
            else "Da_xuat"
        )
        tong_tien = (
            sum(item["so_luong"] * item["gia"] - item["giam"] for item in items)
            - giam_gia
        )

        print(
            f"Creating HoaDon: user_id={user_id}, khach_hang={khach_hang}, tong_tien={tong_tien}"
        )
        c.execute(
            "INSERT INTO HoaDon (user_id, khach_hang, ngay, trang_thai, tong, giam_gia) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, khach_hang, ngay, trang_thai, tong_tien, giam_gia),
        )
        hoadon_id = c.lastrowid

        # Thêm chi tiết hóa đơn vào ChiTietHoaDon
        warnings = []
        for item in items:
            sanpham_id = item["sanpham_id"]
            so_luong = item["so_luong"]
            loai_gia = item["loai_gia"]
            gia = item["gia"]
            giam = item["giam"]
            xuat_hoa_don_item = item["xuat_hoa_don"]
            ghi_chu = item.get("ghi_chu", "")

            print(
                f"Inserting ChiTietHoaDon: hoadon_id={hoadon_id}, sanpham_id={sanpham_id}, gia={item['gia']}"
            )
            c.execute(
                "INSERT INTO ChiTietHoaDon (hoadon_id, sanpham_id, so_luong, loai_gia, gia, giam, xuat_hoa_don, ghi_chu) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    hoadon_id,
                    sanpham_id,
                    so_luong,
                    loai_gia,
                    gia,
                    giam,
                    xuat_hoa_don_item,
                    ghi_chu,
                ),
            )

            # Tính chenh_lech_cong_doan theo logic đúng:
            # - VIP: chênh lệch = 0
            # - Buôn: chênh lệch = 0
            # - Lẻ: chênh lệch = (giá_lẻ - giá_buôn) * số_lượng - giảm_giá
            chenh_lech = 0
            if loai_gia == "le":
                # Lấy cả giá lẻ và giá buôn
                c.execute(
                    "SELECT gia_le, gia_buon FROM SanPham WHERE id = ?", (sanpham_id,)
                )
                result = c.fetchone()
                if result:
                    gia_le_db, gia_buon_db = result
                    chenh_lech = (gia_le_db - gia_buon_db) * so_luong - giam
            # else: VIP và Buôn thì chênh lệch = 0

        # Commit transaction sau khi INSERT
        conn.commit()

        # Luôn cập nhật kho cho tất cả item, và cộng so_du nếu XHĐ=0
        for item in items:
            sanpham_id = item["sanpham_id"]
            so_luong = item["so_luong"]
            gia = item["gia"]
            giam = item["giam"]
            xuat_hoa_don_item = item["xuat_hoa_don"]
            loai_gia = item["loai_gia"]

            # Tính lại chenh_lech để truyền vào LogKho
            # Logic: VIP=0, Buôn=0, Lẻ=(giá_lẻ - giá_buôn)*số_lượng - giảm_giá
            chenh_lech = 0
            if loai_gia == "le":
                c.execute(
                    "SELECT gia_le, gia_buon FROM SanPham WHERE id = ?", (sanpham_id,)
                )
                result = c.fetchone()
                if result:
                    gia_le_db, gia_buon_db = result
                    chenh_lech = (gia_le_db - gia_buon_db) * so_luong - giam

            print(
                f"Calling cap_nhat_kho_sau_ban: sanpham_id={sanpham_id}, so_luong={so_luong}, gia={gia}, chenh_lech={chenh_lech}"
            )
            success, msg = cap_nhat_kho_sau_ban(
                sanpham_id, so_luong, user_id, gia, chenh_lech  # Thêm param chenh_lech
            )
            if not success:
                conn.rollback()
                return False, msg, None

            # Nếu XHĐ=0, cộng tổng tiền vào so_du (tiền user giữ tạm)
            if xuat_hoa_don_item == 0:
                item_total = so_luong * gia - giam
                c.execute(
                    "UPDATE Users SET so_du = so_du + ? WHERE id = ?",
                    (item_total, user_id),
                )
                conn.commit()  # Commit ngay để đảm bảo

        # Tạo hóa đơn thành công (đã kiểm tra tồn kho trước)
        return True, hoadon_id, None

    except Exception as e:
        conn.rollback()
        print(f"Error in tao_hoa_don: {str(e)}")
        return False, str(e), None
    finally:
        print("Closing conn in tao_hoa_don")
        conn.close()


def lay_danh_sach_hoadon(trang_thai=None):
    try:
        conn = ket_noi()
        c = conn.cursor()
        if trang_thai:
            c.execute("SELECT * FROM HoaDon WHERE trang_thai = ?", (trang_thai,))
        else:
            c.execute("SELECT * FROM HoaDon")
        return c.fetchall()
    finally:
        print("Closing conn in lay_danh_sach_hoadon")
        conn.close()


def lay_danh_sach_hoadon(trang_thai=None):
    try:
        conn = ket_noi()
        c = conn.cursor()
        sql = "SELECT hd.id, hd.user_id, u.username, hd.khach_hang, hd.ngay, hd.trang_thai, hd.tong, hd.giam_gia FROM HoaDon hd JOIN Users u ON hd.user_id = u.id"
        if trang_thai:
            sql += " WHERE hd.trang_thai = ?"
            c.execute(sql, (trang_thai,))
        else:
            c.execute(sql)
        return c.fetchall()
    finally:
        print("Closing conn in lay_danh_sach_hoadon")
        conn.close()


def lay_chi_tiet_hoadon(hoadon_id):
    try:
        conn = ket_noi()
        c = conn.cursor()
        c.execute(
            "SELECT c.id, c.hoadon_id, c.sanpham_id, s.ten, c.so_luong, c.loai_gia, c.gia, c.xuat_hoa_don, s.gia_le, c.giam, c.ghi_chu "
            "FROM ChiTietHoaDon c JOIN SanPham s ON c.sanpham_id = s.id WHERE c.hoadon_id = ?",
            (hoadon_id,),
        )
        return c.fetchall()
    finally:
        print("Closing conn in lay_chi_tiet_hoadon")
        conn.close()


def xuat_hoa_don(hoadon_id, user_id):
    try:
        conn = ket_noi()
        c = conn.cursor()
        c.execute("SELECT trang_thai FROM HoaDon WHERE id = ?", (hoadon_id,))
        trang_thai = c.fetchone()[0]
        if trang_thai == "Da_xuat":
            return False, "Hóa đơn đã xuất"

        c.execute("UPDATE HoaDon SET trang_thai = 'Da_xuat' WHERE id = ?", (hoadon_id,))
        conn.commit()
        return True, "Xuất thành công"
    except Exception as e:
        return False, str(e)
    finally:
        print("Closing conn in xuat_hoa_don")
        conn.close()


def lay_chi_tiet_hoadon_da_xuat(user_id, role, tu_ngay=None, den_ngay=None):
    """
    Lấy chi tiết các hóa đơn đã xuất
    - Staff: chỉ xem hóa đơn của mình
    - Admin/Accountant: xem tất cả
    """
    try:
        conn = ket_noi()
        c = conn.cursor()

        sql = """
            SELECT
                hd.ngay,
                u.username,
                ct.loai_gia,
                (ct.so_luong * ct.gia - ct.giam) as tong_tien,
                ct.ghi_chu,
                s.ten as ten_sp,
                ct.so_luong,
                ct.gia
            FROM ChiTietHoaDon ct
            JOIN HoaDon hd ON ct.hoadon_id = hd.id
            JOIN Users u ON hd.user_id = u.id
            JOIN SanPham s ON ct.sanpham_id = s.id
            WHERE hd.trang_thai = 'Da_xuat'
        """

        params = []

        # Nếu là staff thì chỉ xem hóa đơn của mình
        if role == "staff":
            sql += " AND hd.user_id = ?"
            params.append(user_id)

        # Lọc theo ngày
        if tu_ngay:
            sql += " AND date(hd.ngay) >= date(?)"
            params.append(tu_ngay)
        if den_ngay:
            sql += " AND date(hd.ngay) <= date(?)"
            params.append(den_ngay)

        sql += " ORDER BY hd.ngay DESC"

        c.execute(sql, params)
        return c.fetchall()
    finally:
        print("Closing conn in lay_chi_tiet_hoadon_da_xuat")
        conn.close()


def export_hoa_don_excel(file_path, trang_thai=None):
    try:
        conn = ket_noi()
        query = "SELECT * FROM HoaDon"
        if trang_thai:
            query += f" WHERE trang_thai = '{trang_thai}'"
        df = pd.read_sql_query(query, conn)
        df.to_excel(file_path, index=False)
        return True
    except Exception as e:
        print(f"Export error: {e}")
        return False
    finally:
        print("Closing conn in export_hoa_don_excel")
        conn.close()
