from datetime import datetime
from db import ket_noi
from stock import cap_nhat_kho_sau_ban
from utils.db_helpers import db_transaction, execute_query, execute_update
import pandas as pd


def tao_hoa_don(user_id, khach_hang, items, uu_dai, xuat_hoa_don, giam_gia, ngay_ghi_nhan=None):
    """
    Tạo hóa đơn mới với thời gian tùy chỉnh.
    
    Args:
        ngay_ghi_nhan: Thời gian ghi nhận (string format 'YYYY-MM-DD HH:MM:SS').
                       Nếu None, sử dụng thời gian hiện tại.
    """
    try:
        # Kiểm tra dữ liệu items
        for item in items:
            if "gia" not in item or not isinstance(item["gia"], (int, float)):
                print(f"Invalid gia for item {item}: gia must be a number")
                return (
                    False,
                    f"Giá không hợp lệ cho sản phẩm ID {item.get('sanpham_id', 'unknown')}",
                    None,
                )

        errors = []
        # Kiểm tra tồn kho trước khi tạo hóa đơn (đọc trong 1 transaction để đồng nhất)
        with db_transaction() as (conn, c):
            for item in items:
                sanpham_id = item["sanpham_id"]
                so_luong = item["so_luong"]
                c.execute("SELECT ten, ton_kho FROM SanPham WHERE id = ?", (sanpham_id,))
                result = c.fetchone()
                if not result:
                    errors.append(f"Sản phẩm ID {sanpham_id} không tồn tại")
                    continue
                ten_sp, ton_kho = result
                if ton_kho < so_luong:
                    errors.append(
                        f"Sản phẩm '{ten_sp}' không đủ số lượng!\n"
                        f"  - Tồn kho: {ton_kho}\n"
                        f"  - Yêu cầu: {so_luong}\n"
                        f"  - Thiếu: {so_luong - ton_kho}"
                    )
            # Nếu có lỗi tồn kho thì raise để thoát transaction và trả về lỗi
            if errors:
                raise ValueError("; ".join(errors))

            # Tính toán tổng tiền theo logic hiện tại
            # ✅ Sử dụng thời gian từ tham số hoặc thời gian hiện tại
            if ngay_ghi_nhan:
                ngay = ngay_ghi_nhan
            else:
                ngay = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            trang_thai = (
                "Chua_xuat"
                if any(item.get("xuat_hoa_don", 1) == 0 for item in items)
                else "Da_xuat"
            )

            tong_tien_raw = sum(item["so_luong"] * item["gia"] for item in items)
            tong_giam_item = sum(item.get("giam", 0) for item in items)
            tong_legacy = tong_tien_raw - tong_giam_item - (giam_gia or 0)
            uu_dai_val = uu_dai or 0
            tong_sau_uu_dai = tong_tien_raw - uu_dai_val
            tong_cuoi = tong_tien_raw - uu_dai_val - tong_giam_item - (giam_gia or 0)

            print(
                f"Creating HoaDon: user_id={user_id}, khach_hang={khach_hang}, tong={tong_legacy}"
            )
            # Chèn hóa đơn với cột cũ để đảm bảo tương thích
            c.execute(
                "INSERT INTO HoaDon (user_id, khach_hang, ngay, trang_thai, tong, giam_gia) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, khach_hang, ngay, trang_thai, tong_legacy, giam_gia),
            )
            hoadon_id = c.lastrowid

            # Cố gắng cập nhật các cột mới nếu tồn tại (bỏ qua lỗi nếu DB cũ chưa có)
            try:
                c.execute(
                    "UPDATE HoaDon SET tong_tien = ?, uu_dai = ?, tong_sau_uu_dai = ?, tong_cuoi = ? WHERE id = ?",
                    (tong_tien_raw, uu_dai_val, tong_sau_uu_dai, tong_cuoi, hoadon_id),
                )
            except Exception:
                pass

            # Thêm chi tiết hóa đơn vào ChiTietHoaDon
            for item in items:
                sanpham_id = item["sanpham_id"]
                so_luong = item["so_luong"]
                loai_gia = item["loai_gia"]
                gia = item["gia"]
                giam = item.get("giam", 0)
                xuat_hoa_don_item = item.get("xuat_hoa_don", 1)
                ghi_chu = item.get("ghi_chu", "")

                print(
                    f"Inserting ChiTietHoaDon: hoadon_id={hoadon_id}, sanpham_id={sanpham_id}, gia={gia}"
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

                # Tính chênh lệch công đoàn cho loại giá lẻ
                if loai_gia == "le":
                    c.execute(
                        "SELECT gia_le, gia_buon FROM SanPham WHERE id = ?",
                        (sanpham_id,),
                    )
                    result = c.fetchone()
                    if result:
                        gia_le_db, gia_buon_db = result
                        _ = (gia_le_db - gia_buon_db) * so_luong - giam

        # Sau khi tạo hóa đơn và chi tiết thành công, cập nhật kho và sổ quỹ theo từng item
        for item in items:
            sanpham_id = item["sanpham_id"]
            so_luong = item["so_luong"]
            gia = item["gia"]
            giam = item.get("giam", 0)
            xuat_hoa_don_item = item.get("xuat_hoa_don", 1)
            loai_gia = item["loai_gia"]

            # Tính lại chênh lệch để ghi log kho nếu cần
            chenh_lech = 0
            if loai_gia == "le":
                result = execute_query(
                    "SELECT gia_le, gia_buon FROM SanPham WHERE id = ?",
                    (sanpham_id,),
                    fetch_one=True,
                )
                if result:
                    gia_le_db, gia_buon_db = result
                    chenh_lech = (gia_le_db - gia_buon_db) * so_luong - giam

            print(
                f"Calling cap_nhat_kho_sau_ban: sanpham_id={sanpham_id}, so_luong={so_luong}, gia={gia}, chenh_lech={chenh_lech}"
            )
            success, msg = cap_nhat_kho_sau_ban(
                sanpham_id, so_luong, user_id, gia, chenh_lech
            )
            if not success:
                return False, msg, None

            # Nếu XHĐ=0, cộng tổng tiền vào so_du (tiền user giữ tạm)
            if xuat_hoa_don_item == 0:
                item_total = so_luong * gia - giam
                execute_update(
                    "UPDATE Users SET so_du = so_du + ? WHERE id = ?",
                    (item_total, user_id),
                )

        return True, hoadon_id, None
    except ValueError as ve:
        # Lỗi kiểm tra tồn kho
        return False, str(ve).replace("; ", "\n\n"), None
    except Exception as e:
        print(f"Error in tao_hoa_don: {str(e)}")
        return False, str(e), None


def lay_danh_sach_hoadon(trang_thai=None):
    sql = (
        "SELECT hd.id, hd.user_id, u.username, hd.khach_hang, hd.ngay, hd.trang_thai, hd.tong, hd.giam_gia "
        "FROM HoaDon hd JOIN Users u ON hd.user_id = u.id"
    )
    params = None
    if trang_thai:
        sql += " WHERE hd.trang_thai = ?"
        params = (trang_thai,)
    return execute_query(sql, params, fetch_all=True) or []


def lay_chi_tiet_hoadon(hoadon_id):
    return (
        execute_query(
            "SELECT c.id, c.hoadon_id, c.sanpham_id, s.ten, c.so_luong, c.loai_gia, c.gia, c.xuat_hoa_don, s.gia_le, c.giam, c.ghi_chu "
            "FROM ChiTietHoaDon c JOIN SanPham s ON c.sanpham_id = s.id WHERE c.hoadon_id = ?",
            (hoadon_id,),
            fetch_all=True,
        )
        or []
    )


def xuat_hoa_don(hoadon_id, user_id):
    try:
        with db_transaction() as (conn, c):
            c.execute("SELECT trang_thai FROM HoaDon WHERE id = ?", (hoadon_id,))
            row = c.fetchone()
            if not row:
                return False, "Không tìm thấy hóa đơn"
            trang_thai = row[0]
            if trang_thai == "Da_xuat":
                return False, "Hóa đơn đã xuất"
            c.execute("UPDATE HoaDon SET trang_thai = 'Da_xuat' WHERE id = ?", (hoadon_id,))
        return True, "Xuất thành công"
    except Exception as e:
        return False, str(e)


def lay_chi_tiet_hoadon_da_xuat(user_id, role, tu_ngay=None, den_ngay=None):
    """
    Lấy chi tiết các hóa đơn đã xuất
    - Staff: chỉ xem hóa đơn của mình
    - Admin/Accountant: xem tất cả
    """
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
    if role == "staff":
        sql += " AND hd.user_id = ?"
        params.append(user_id)
    if tu_ngay:
        sql += " AND date(hd.ngay) >= date(?)"
        params.append(tu_ngay)
    if den_ngay:
        sql += " AND date(hd.ngay) <= date(?)"
        params.append(den_ngay)

    sql += " ORDER BY hd.ngay DESC"
    return execute_query(sql, tuple(params) if params else None, fetch_all=True) or []


def sua_hoa_don(hoadon_id, ngay=None, khach_hang=None, ghi_chu=None):
    """
    Sửa thông tin hóa đơn (chỉ cho admin).
    
    Args:
        hoadon_id: ID hóa đơn cần sửa
        ngay: Ngày giờ mới (format 'YYYY-MM-DD HH:MM:SS') hoặc None nếu không đổi
        khach_hang: Tên khách hàng mới hoặc None nếu không đổi
        ghi_chu: Ghi chú mới hoặc None nếu không đổi
    """
    try:
        updates = []
        params = []
        
        if ngay is not None:
            updates.append("ngay = ?")
            params.append(ngay)
        
        if khach_hang is not None:
            updates.append("khach_hang = ?")
            params.append(khach_hang)
        
        if ghi_chu is not None:
            updates.append("ghi_chu = ?")
            params.append(ghi_chu)
        
        if not updates:
            return True  # Không có gì để cập nhật
        
        params.append(hoadon_id)
        sql = f"UPDATE HoaDon SET {', '.join(updates)} WHERE id = ?"
        
        success = execute_update(sql, tuple(params))
        return success
    except Exception as e:
        print(f"Lỗi sửa hóa đơn: {e}")
        return False


def xoa_hoa_don(hoadon_id):
    """
    Xóa hóa đơn và tất cả chi tiết hóa đơn liên quan (chỉ cho admin).
    Lưu ý: Cần cân nhắc việc hoàn trả tồn kho.
    """
    try:
        with db_transaction() as (conn, c):
            # Xóa chi tiết hóa đơn trước
            c.execute("DELETE FROM ChiTietHoaDon WHERE hoadon_id = ?", (hoadon_id,))
            # Xóa hóa đơn
            c.execute("DELETE FROM HoaDon WHERE id = ?", (hoadon_id,))
        return True
    except Exception as e:
        print(f"Lỗi xóa hóa đơn: {e}")
        return False


def sua_chi_tiet_hoa_don(chitiet_id, so_luong=None, gia=None, giam=None, ghi_chu=None):
    """
    Sửa chi tiết hóa đơn (chỉ cho admin).
    
    Args:
        chitiet_id: ID chi tiết hóa đơn cần sửa
        so_luong: Số lượng mới hoặc None nếu không đổi
        gia: Giá mới hoặc None nếu không đổi
        giam: Giảm giá mới hoặc None nếu không đổi
        ghi_chu: Ghi chú mới hoặc None nếu không đổi
    """
    try:
        updates = []
        params = []
        
        if so_luong is not None:
            updates.append("so_luong = ?")
            params.append(so_luong)
        
        if gia is not None:
            updates.append("gia = ?")
            params.append(gia)
        
        if giam is not None:
            updates.append("giam = ?")
            params.append(giam)
        
        if ghi_chu is not None:
            updates.append("ghi_chu = ?")
            params.append(ghi_chu)
        
        if not updates:
            return True  # Không có gì để cập nhật
        
        params.append(chitiet_id)
        sql = f"UPDATE ChiTietHoaDon SET {', '.join(updates)} WHERE id = ?"
        
        success = execute_update(sql, tuple(params))
        return success
    except Exception as e:
        print(f"Lỗi sửa chi tiết hóa đơn: {e}")
        return False


def xoa_chi_tiet_hoa_don(chitiet_id):
    """
    Xóa một chi tiết hóa đơn (chỉ cho admin).
    Lưu ý: Cần cân nhắc việc hoàn trả tồn kho.
    """
    try:
        success = execute_update("DELETE FROM ChiTietHoaDon WHERE id = ?", (chitiet_id,))
        return success
    except Exception as e:
        print(f"Lỗi xóa chi tiết hóa đơn: {e}")
        return False


def export_hoa_don_excel(file_path, trang_thai=None):
    try:
        conn = ket_noi()
        query = "SELECT * FROM HoaDon"
        params = None
        if trang_thai:
            query += " WHERE trang_thai = ?"
            params = (trang_thai,)
        df = pd.read_sql_query(query, conn, params=params)
        df.to_excel(file_path, index=False)
        return True
    except Exception as e:
        print(f"Export error: {e}")
        return False
    finally:
        conn.close()
