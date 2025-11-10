from datetime import datetime
from db import ket_noi
from utils.db_helpers import execute_query, db_transaction


def lay_ton_kho(sanpham_id):
    """
    Lấy số lượng tồn kho của một sản phẩm

    Args:
        sanpham_id: ID sản phẩm

    Returns:
        int: Số lượng tồn kho, hoặc None nếu không tìm thấy
    """
    result = execute_query(
        "SELECT ton_kho FROM SanPham WHERE id = ?", (sanpham_id,), fetch_one=True
    )
    return result[0] if result else None


def cap_nhat_ton_kho(sanpham_id, so_luong_moi):
    """
    Cập nhật tồn kho của một sản phẩm

    Args:
        sanpham_id: ID sản phẩm
        so_luong_moi: Số lượng tồn kho mới

    Returns:
        bool: True nếu thành công, False nếu thất bại
    """
    try:
        execute_query(
            "UPDATE SanPham SET ton_kho = ? WHERE id = ?", (so_luong_moi, sanpham_id)
        )
        return True
    except:
        return False


def cap_nhat_kho_sau_ban(sanpham_id, so_luong, user_id, gia_ap_dung, chenh_lech=0):
    try:
        with db_transaction() as (conn, c):
            # Kiểm tra tồn kho
            c.execute("SELECT ton_kho FROM SanPham WHERE id = ?", (sanpham_id,))
            result = c.fetchone()
            if not result:
                return False, f"Sản phẩm ID {sanpham_id} không tồn tại"
            ton_kho = result[0]

            if ton_kho < so_luong:
                return False, f"Tồn kho không đủ: chỉ còn {ton_kho}, yêu cầu {so_luong}"

            # Cập nhật tồn kho
            c.execute(
                "UPDATE SanPham SET ton_kho = ton_kho - ? WHERE id = ?",
                (so_luong, sanpham_id),
            )

            # Ghi log kho với chenh_lech_cong_doan
            ngay = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("SELECT ton_kho FROM SanPham WHERE id = ?", (sanpham_id,))
            ton_sau = c.fetchone()[0]  # ton_sau sau update
            ton_truoc = ton_kho  # ton_truoc trước update
            c.execute(
                "INSERT INTO LogKho (sanpham_id, user_id, ngay, hanh_dong, so_luong, ton_truoc, ton_sau, gia_ap_dung, chenh_lech_cong_doan) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    sanpham_id,
                    user_id,
                    ngay,
                    "xuat",
                    so_luong,
                    ton_truoc,
                    ton_sau,
                    gia_ap_dung,
                    chenh_lech,
                ),
            )

        return True, "Cập nhật kho thành công"
    except Exception as e:
        return False, f"Lỗi cập nhật kho: {str(e)}"


def lay_san_pham_chua_xuat():
    return (
        execute_query(
            "SELECT c.hoadon_id, c.sanpham_id, s.ten, c.so_luong, c.loai_gia, c.gia "
            "FROM ChiTietHoaDon c JOIN SanPham s ON c.sanpham_id = s.id "
            "WHERE c.xuat_hoa_don = 0",
            fetch_all=True,
        )
        or []
    )


def lay_san_pham_chua_xuat_theo_loai_gia(loai_gia):
    """
    Lấy tổng số lượng sản phẩm chưa xuất hóa đơn theo loại giá
    Returns: [(ten_san_pham, tong_so_luong), ...]
    """
    return (
        execute_query(
            """
        SELECT s.ten, SUM(c.so_luong) as tong_sl
        FROM ChiTietHoaDon c
        JOIN SanPham s ON c.sanpham_id = s.id
        WHERE c.xuat_hoa_don = 0 AND c.loai_gia = ?
        GROUP BY s.ten
        ORDER BY s.ten
        """,
            (loai_gia,),
            fetch_all=True,
        )
        or []
    )


def xuat_bo_san_pham(hoadon_id, sanpham_id, user_id, so_luong, gia, chenh_lech):
    try:
        with db_transaction() as (conn, c):
            # Cập nhật trạng thái xuất hóa đơn
            c.execute(
                "UPDATE ChiTietHoaDon SET xuat_hoa_don = 1 WHERE hoadon_id = ? AND sanpham_id = ?",
                (hoadon_id, sanpham_id),
            )

            # Ghi log công đoạn
            ngay = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute(
                "INSERT INTO CongDoan (sanpham_id, user_id, ngay, so_luong, chenh_lech) "
                "VALUES (?, ?, ?, ?, ?)",
                (sanpham_id, user_id, ngay, so_luong, chenh_lech),
            )

            # Cập nhật số dư user: trừ so_du (giảm khi xuất bổ)
            tong_tien = so_luong * (gia + chenh_lech)
            c.execute(
                "UPDATE Users SET so_du = so_du - ? WHERE id = ?", (tong_tien, user_id)
            )

        return True, "Xuất bổ thành công"
    except Exception as e:
        return False, f"Lỗi xuất bổ: {str(e)}"


def xuat_bo_san_pham_theo_ten(
    ten_sanpham,
    loai_gia,
    so_luong_xuat,
    user_id,
    chenh_lech,
    loai_gia_phu=None,
    so_luong_phu=0,
    loai_gia_phu2=None,
    so_luong_phu2=0,
):
    """
    Xuất bổ sản phẩm theo tên sản phẩm, loại giá và số lượng.
    Tự động tìm và xuất từ các hóa đơn chưa xuất theo FIFO.

    Logic mới:
    - Giá lẻ: chỉ lấy từ bảng chưa xuất giá lẻ
    - Giá buôn: ưu tiên bảng chưa xuất giá buôn trước, không đủ thì lấy từ bảng chưa xuất giá lẻ
    - Giá VIP: ưu tiên bảng giá VIP trước, không đủ qua bảng chưa xuất giá buôn, hiện thông báo xác nhận mượn
    """
    try:
        with db_transaction() as (conn, c):
            # Lấy thông tin sản phẩm với giá các loại
            c.execute(
                "SELECT id, gia_vip, gia_buon, gia_le FROM SanPham WHERE ten = ?",
                (ten_sanpham,),
            )
            result = c.fetchone()
            if not result:
                return False, f"Sản phẩm '{ten_sanpham}' không tồn tại"
            sanpham_id, gia_vip, gia_buon, gia_le = result

            # Lấy các chi tiết hóa đơn chưa xuất theo loại giá chính (FIFO - cũ nhất trước)
            c.execute(
                """
                SELECT c.id, c.hoadon_id, c.so_luong, c.gia
                FROM ChiTietHoaDon c
                JOIN HoaDon h ON c.hoadon_id = h.id
                WHERE c.sanpham_id = ? AND c.loai_gia = ? AND c.xuat_hoa_don = 0
                ORDER BY h.ngay ASC
                """,
                (sanpham_id, loai_gia),
            )
            chi_tiet_list = c.fetchall()

            if not chi_tiet_list:
                return (
                    False,
                    f"Không có sản phẩm '{ten_sanpham}' với loại giá '{loai_gia}' chưa xuất",
                )

            # Tính tổng số lượng có sẵn từ loại giá chính
            tong_sl_co_san = sum(row[2] for row in chi_tiet_list)

            # Logic mới theo yêu cầu
            if loai_gia == "le":
                # Giá lẻ: chỉ lấy từ bảng chưa xuất giá lẻ
                if tong_sl_co_san < so_luong_xuat:
                    return (
                        False,
                        f"Sản phẩm '{ten_sanpham}' không đủ số lượng giá lẻ (có {tong_sl_co_san}, cần {so_luong_xuat})",
                    )

            elif loai_gia == "buon":
                # Giá buôn: ưu tiên bảng chưa xuất giá buôn trước, không đủ thì lấy từ bảng chưa xuất giá lẻ
                if tong_sl_co_san < so_luong_xuat:
                    sl_thieu = so_luong_xuat - tong_sl_co_san

                    # Kiểm tra số lượng từ giá lẻ
                    c.execute(
                        """
                        SELECT SUM(c.so_luong)
                        FROM ChiTietHoaDon c
                        WHERE c.sanpham_id = ? AND c.loai_gia = 'le' AND c.xuat_hoa_don = 0
                        """,
                        (sanpham_id,),
                    )
                    sl_le_co = c.fetchone()[0] or 0

                    if sl_le_co < sl_thieu:
                        return (
                            False,
                            f"Sản phẩm '{ten_sanpham}' không đủ số lượng (buôn: {tong_sl_co_san}, lẻ: {sl_le_co}, cần: {so_luong_xuat})",
                        )

                    # Lưu thông tin để lấy từ giá lẻ
                    loai_gia_phu = "le"
                    so_luong_phu = sl_thieu

            elif loai_gia == "vip":
                # Giá VIP: ưu tiên bảng giá VIP trước, không đủ qua bảng chưa xuất giá buôn, hiện thông báo xác nhận mượn
                if tong_sl_co_san < so_luong_xuat:
                    sl_thieu = so_luong_xuat - tong_sl_co_san

                    # Kiểm tra số lượng từ giá buôn
                    c.execute(
                        """
                        SELECT SUM(c.so_luong)
                        FROM ChiTietHoaDon c
                        WHERE c.sanpham_id = ? AND c.loai_gia = 'buon' AND c.xuat_hoa_don = 0
                        """,
                        (sanpham_id,),
                    )
                    sl_buon_co = c.fetchone()[0] or 0

                    if sl_buon_co > 0:
                        loai_gia_phu = "buon"
                        so_luong_phu = min(sl_thieu, sl_buon_co)
                        sl_thieu -= so_luong_phu

                    # Nếu vẫn thiếu, kiểm tra số lượng từ giá lẻ
                    if sl_thieu > 0:
                        c.execute(
                            """
                            SELECT SUM(c.so_luong)
                            FROM ChiTietHoaDon c
                            WHERE c.sanpham_id = ? AND c.loai_gia = 'le' AND c.xuat_hoa_don = 0
                            """,
                            (sanpham_id,),
                        )
                        sl_le_co = c.fetchone()[0] or 0

                        if sl_le_co > 0:
                            loai_gia_phu2 = "le"
                            so_luong_phu2 = min(sl_thieu, sl_le_co)
                            sl_thieu -= so_luong_phu2

                    # Kiểm tra tổng số lượng
                    tong_sl_co = tong_sl_co_san + so_luong_phu + so_luong_phu2
                    if tong_sl_co < so_luong_xuat:
                        return (
                            False,
                            f"Không đủ số lượng (VIP: {tong_sl_co_san}, buôn: {so_luong_phu}, lẻ: {so_luong_phu2}, cần: {so_luong_xuat})",
                        )

        # Xuất bổ theo FIFO từ loại giá chính
        so_luong_con_lai = so_luong_xuat
        tong_tien_xuat = 0
        ngay = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Tính giá chênh lệch nếu xuất VIP từ các nguồn khác
        chenh_buon = (
            gia_vip - gia_buon
            if loai_gia == "vip" and loai_gia_phu == "buon"
            else chenh_lech
        )
        chenh_le = (
            gia_vip - gia_le
            if loai_gia == "vip" and loai_gia_phu2 == "le"
            else chenh_lech
        )

        # Xuất từ loại giá chính trước
        for chi_tiet_id, hoadon_id, sl_hien_tai, gia in chi_tiet_list:
            if so_luong_con_lai <= 0:
                break

            sl_xuat = min(so_luong_con_lai, sl_hien_tai)

            if sl_xuat == sl_hien_tai:
                # Xuất hết dòng này
                c.execute(
                    "UPDATE ChiTietHoaDon SET xuat_hoa_don = 1 WHERE id = ?",
                    (chi_tiet_id,),
                )
            else:
                # Chia dòng: tạo dòng mới đã xuất, giảm số lượng dòng cũ
                c.execute(
                    "UPDATE ChiTietHoaDon SET so_luong = ? WHERE id = ?",
                    (sl_hien_tai - sl_xuat, chi_tiet_id),
                )
                # Tạo dòng mới đã xuất
                c.execute(
                    "SELECT sanpham_id, loai_gia, gia, giam, ghi_chu FROM ChiTietHoaDon WHERE id = ?",
                    (chi_tiet_id,),
                )
                sp_id, lg, g, giam, ghi_chu = c.fetchone()
                c.execute(
                    """
                    INSERT INTO ChiTietHoaDon (hoadon_id, sanpham_id, so_luong, loai_gia, gia, giam, xuat_hoa_don, ghi_chu)
                    VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (hoadon_id, sp_id, sl_xuat, lg, g, giam, ghi_chu),
                )

            tong_tien_xuat += sl_xuat * gia
            so_luong_con_lai -= sl_xuat

        # Nếu còn thiếu và có loại giá phụ, xuất từ loại giá phụ
        if so_luong_con_lai > 0 and loai_gia_phu and so_luong_phu > 0:
            # Lấy các chi tiết hóa đơn chưa xuất theo loại giá phụ (FIFO)
            c.execute(
                """
                SELECT c.id, c.hoadon_id, c.so_luong, c.gia
                FROM ChiTietHoaDon c
                JOIN HoaDon h ON c.hoadon_id = h.id
                WHERE c.sanpham_id = ? AND c.loai_gia = ? AND c.xuat_hoa_don = 0
                ORDER BY h.ngay ASC
                """,
                (sanpham_id, loai_gia_phu),
            )
            chi_tiet_phu_list = c.fetchall()

            for chi_tiet_id, hoadon_id, sl_hien_tai, gia in chi_tiet_phu_list:
                if so_luong_con_lai <= 0:
                    break

                sl_xuat = min(so_luong_con_lai, sl_hien_tai)

                if sl_xuat == sl_hien_tai:
                    # Xuất hết dòng này
                    c.execute(
                        "UPDATE ChiTietHoaDon SET xuat_hoa_don = 1 WHERE id = ?",
                        (chi_tiet_id,),
                    )
                else:
                    # Chia dòng: tạo dòng mới đã xuất, giảm số lượng dòng cũ
                    c.execute(
                        "UPDATE ChiTietHoaDon SET so_luong = ? WHERE id = ?",
                        (sl_hien_tai - sl_xuat, chi_tiet_id),
                    )
                    # Tạo dòng mới đã xuất
                    c.execute(
                        "SELECT sanpham_id, loai_gia, gia, giam, ghi_chu FROM ChiTietHoaDon WHERE id = ?",
                        (chi_tiet_id,),
                    )
                    sp_id, lg, g, giam, ghi_chu = c.fetchone()
                    c.execute(
                        """
                        INSERT INTO ChiTietHoaDon (hoadon_id, sanpham_id, so_luong, loai_gia, gia, giam, xuat_hoa_don, ghi_chu)
                        VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                        """,
                        (hoadon_id, sp_id, sl_xuat, lg, g, giam, ghi_chu),
                    )

                tong_tien_xuat += sl_xuat * gia
                so_luong_con_lai -= sl_xuat

        # Nếu còn thiếu và có loại giá phụ thứ 2, xuất từ loại giá phụ thứ 2
        if so_luong_con_lai > 0 and loai_gia_phu2 and so_luong_phu2 > 0:
            # Lấy các chi tiết hóa đơn chưa xuất theo loại giá phụ thứ 2 (FIFO)
            c.execute(
                """
                SELECT c.id, c.hoadon_id, c.so_luong, c.gia
                FROM ChiTietHoaDon c
                JOIN HoaDon h ON c.hoadon_id = h.id
                WHERE c.sanpham_id = ? AND c.loai_gia = ? AND c.xuat_hoa_don = 0
                ORDER BY h.ngay ASC
                """,
                (sanpham_id, loai_gia_phu2),
            )
            chi_tiet_phu2_list = c.fetchall()

            for chi_tiet_id, hoadon_id, sl_hien_tai, gia in chi_tiet_phu2_list:
                if so_luong_con_lai <= 0:
                    break

                sl_xuat = min(so_luong_con_lai, sl_hien_tai)

                if sl_xuat == sl_hien_tai:
                    # Xuất hết dòng này
                    c.execute(
                        "UPDATE ChiTietHoaDon SET xuat_hoa_don = 1 WHERE id = ?",
                        (chi_tiet_id,),
                    )
                else:
                    # Chia dòng: tạo dòng mới đã xuất, giảm số lượng dòng cũ
                    c.execute(
                        "UPDATE ChiTietHoaDon SET so_luong = ? WHERE id = ?",
                        (sl_hien_tai - sl_xuat, chi_tiet_id),
                    )
                    # Tạo dòng mới đã xuất
                    c.execute(
                        "SELECT sanpham_id, loai_gia, gia, giam, ghi_chu FROM ChiTietHoaDon WHERE id = ?",
                        (chi_tiet_id,),
                    )
                    sp_id, lg, g, giam, ghi_chu = c.fetchone()
                    c.execute(
                        """
                        INSERT INTO ChiTietHoaDon (hoadon_id, sanpham_id, so_luong, loai_gia, gia, giam, xuat_hoa_don, ghi_chu)
                        VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                        """,
                        (hoadon_id, sp_id, sl_xuat, lg, g, giam, ghi_chu),
                    )

                tong_tien_xuat += sl_xuat * gia
                so_luong_con_lai -= sl_xuat

        # Ghi log công đoàn cho từng phần theo logic mới
        sl_chinh = so_luong_xuat - (so_luong_phu + so_luong_phu2)
        if sl_chinh > 0:
            c.execute(
                "INSERT INTO CongDoan (sanpham_id, user_id, ngay, so_luong, chenh_lech) "
                "VALUES (?, ?, ?, ?, ?)",
                (sanpham_id, user_id, ngay, sl_chinh, chenh_lech),
            )
            # Ghi log vào LogKho cho loại giá chính
            c.execute(
                "INSERT INTO LogKho (sanpham_id, user_id, ngay, hanh_dong, so_luong, ton_truoc, ton_sau, gia_ap_dung, chenh_lech_cong_doan, loai_gia) "
                "VALUES (?, ?, ?, 'xuatbo', ?, 0, 0, 0, ?, ?)",
                (sanpham_id, user_id, ngay, sl_chinh, chenh_lech, loai_gia),
            )

        # Tính chênh lệch công đoàn theo yêu cầu mới
        # Xử lý loại giá phụ cho cả "buon" và "vip"
        if so_luong_phu > 0 and loai_gia_phu:
            if loai_gia == "vip":
                # Chênh lệch = (giá buôn - giá VIP) x số lượng mượn chưa xuất giá buôn
                chenh_buon = gia_buon - gia_vip
                c.execute(
                    "INSERT INTO CongDoan (sanpham_id, user_id, ngay, so_luong, chenh_lech) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (sanpham_id, user_id, ngay, so_luong_phu, chenh_buon),
                )
                # Ghi log vào LogKho cho loại giá phụ (buôn)
                c.execute(
                    "INSERT INTO LogKho (sanpham_id, user_id, ngay, hanh_dong, so_luong, ton_truoc, ton_sau, gia_ap_dung, chenh_lech_cong_doan, loai_gia) "
                    "VALUES (?, ?, ?, 'xuatbo', ?, 0, 0, 0, ?, ?)",
                    (sanpham_id, user_id, ngay, so_luong_phu, chenh_buon, loai_gia_phu),
                )
            elif loai_gia == "buon" and loai_gia_phu == "le":
                # Xuất buôn từ giá lẻ - không có chênh lệch công đoạn
                c.execute(
                    "INSERT INTO LogKho (sanpham_id, user_id, ngay, hanh_dong, so_luong, ton_truoc, ton_sau, gia_ap_dung, chenh_lech_cong_doan, loai_gia) "
                    "VALUES (?, ?, ?, 'xuatbo', ?, 0, 0, 0, 0, ?)",
                    (sanpham_id, user_id, ngay, so_luong_phu, loai_gia_phu),
                )

        if so_luong_phu2 > 0 and loai_gia_phu2:
            if loai_gia == "vip":
                # Chênh lệch = (giá lẻ - giá VIP) x số lượng mượn bảng chưa xuất giá lẻ
                chenh_le = gia_le - gia_vip
                c.execute(
                    "INSERT INTO CongDoan (sanpham_id, user_id, ngay, so_luong, chenh_lech) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (sanpham_id, user_id, ngay, so_luong_phu2, chenh_le),
                )
                # Ghi log vào LogKho cho loại giá phụ 2 (lẻ)
                c.execute(
                    "INSERT INTO LogKho (sanpham_id, user_id, ngay, hanh_dong, so_luong, ton_truoc, ton_sau, gia_ap_dung, chenh_lech_cong_doan, loai_gia) "
                    "VALUES (?, ?, ?, 'xuatbo', ?, 0, 0, 0, ?, ?)",
                    (sanpham_id, user_id, ngay, so_luong_phu2, chenh_le, loai_gia_phu2),
                )

        # Cập nhật số dư user: trừ so_du
        tong_tien_giam = tong_tien_xuat + (so_luong_xuat * chenh_lech)
        c.execute(
            "UPDATE Users SET so_du = so_du - ? WHERE id = ?", (tong_tien_giam, user_id)
        )

        # Kiểm tra và cập nhật trạng thái hóa đơn
        for _, hoadon_id, _, _ in chi_tiet_list:
            c.execute(
                "SELECT COUNT(*) FROM ChiTietHoaDon WHERE hoadon_id = ? AND xuat_hoa_don = 0",
                (hoadon_id,),
            )
            count = c.fetchone()[0]
            if count == 0:
                c.execute(
                    "UPDATE HoaDon SET trang_thai = 'Da_xuat' WHERE id = ?",
                    (hoadon_id,),
                )

        return True, f"Xuất bổ thành công {so_luong_xuat} {ten_sanpham}"
    except Exception as e:
        return False, f"Lỗi xuất bổ: {str(e)}"


def lay_tong_chua_xuat_theo_sp():
    return (
        execute_query(
            "SELECT s.id, s.ten, SUM(c.so_luong) "
            "FROM ChiTietHoaDon c JOIN SanPham s ON c.sanpham_id = s.id "
            "WHERE c.xuat_hoa_don = 0 GROUP BY s.id, s.ten",
            fetch_all=True,
        )
        or []
    )


def lay_bao_cao_cong_doan(tu_ngay=None, den_ngay=None):
    sql = "SELECT id, sanpham_id, user_id, ngay, so_luong, chenh_lech FROM CongDoan WHERE 1=1"
    params = []
    if tu_ngay:
        sql += " AND ngay >= ?"
        params.append(tu_ngay)
    if den_ngay:
        sql += " AND ngay <= ?"
        params.append(den_ngay)
    data = execute_query(sql, tuple(params) if params else None, fetch_all=True) or []

    sql_tong = "SELECT SUM(chenh_lech * so_luong) FROM CongDoan WHERE 1=1"
    if tu_ngay:
        sql_tong += " AND ngay >= ?"
    if den_ngay:
        sql_tong += " AND ngay <= ?"
    result = execute_query(sql_tong, tuple(params) if params else None, fetch_one=True)
    tong = result[0] if result and result[0] is not None else 0
    return data, tong
