from db import ket_noi
import pandas as pd
from utils.db_helpers import execute_query, db_transaction


def them_sanpham(ten, gia_le, gia_buon, gia_vip, ton_kho=0, nguong_buon=0):
    # ✅ Validate input
    if gia_le < 0 or gia_buon < 0 or gia_vip < 0:
        print("Lỗi: Giá không được âm")
        return False
    if ton_kho < 0 or nguong_buon < 0:
        print("Lỗi: Số lượng không được âm")
        return False

    try:
        with db_transaction() as (conn, c):
            c.execute("SELECT id, ton_kho FROM SanPham WHERE ten=?", (ten,))
            row = c.fetchone()
            if row:
                ton_moi = row[1] + ton_kho
                c.execute("UPDATE SanPham SET ton_kho=? WHERE id=?", (ton_moi, row[0]))
            else:
                c.execute(
                    """INSERT INTO SanPham (ten, gia_le, gia_buon, gia_vip, ton_kho, nguong_buon)
                             VALUES (?, ?, ?, ?, ?, ?)""",
                    (ten, gia_le, gia_buon, gia_vip, ton_kho, nguong_buon),
                )
        return True
    except Exception as e:
        print("Lỗi thêm sản phẩm:", e)
        return False


def cap_nhat_ton(product_id, ton_moi):
    # ✅ Validate input
    if ton_moi < 0:
        print("Lỗi: Tồn kho không được âm")
        return False

    try:
        with db_transaction() as (conn, c):
            c.execute("UPDATE SanPham SET ton_kho=? WHERE id=?", (ton_moi, product_id))
        return True
    except Exception as e:
        print(f"Lỗi cập nhật tồn kho: {e}")
        return False


def tim_sanpham(keyword):
    return (
        execute_query(
            "SELECT * FROM SanPham WHERE ten LIKE ?",
            ("%" + keyword + "%",),
            fetch_all=True,
        )
        or []
    )


def lay_tat_ca_sanpham():
    return (
        execute_query(
            "SELECT id, ten, gia_le, gia_buon, gia_vip, ton_kho, nguong_buon FROM SanPham",
            fetch_all=True,
        )
        or []
    )


def lay_danh_sach_ten_sanpham():
    try:
        rows = execute_query("SELECT ten FROM SanPham", fetch_all=True) or []
        return [row[0] for row in rows]
    except Exception:
        return []


def import_sanpham_from_dataframe(df, user_id=None):
    """Import sản phẩm từ DataFrame và lưu lịch sử thay đổi giá

    Args:
        df: DataFrame với các cột: ten, gia_le, gia_buon, gia_vip, ton_kho, nguong_buon
        user_id: ID của user thực hiện import (để lưu lịch sử)
    """
    df.columns = df.columns.str.strip().str.lower()
    mapping = {
        "tên": "ten",
        "tên sp": "ten",
        "ten sp": "ten",
        "giá lẻ": "gia_le",
        "gia le": "gia_le",
        "giá buôn": "gia_buon",
        "gia buon": "gia_buon",
        "giá vip": "gia_vip",
        "gia vip": "gia_vip",
        "tồn kho": "ton_kho",
        "ton kho": "ton_kho",
        "ngưỡng buôn": "nguong_buon",
        "nguong buon": "nguong_buon",
    }
    df.rename(columns=mapping, inplace=True)
    required = ["ten", "gia_le", "gia_buon", "gia_vip"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Thiếu cột bắt buộc: {col}")

    from datetime import datetime

    ngay_import = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with db_transaction() as (conn, c):
            for _, row in df.iterrows():
                ten = row["ten"]
                gia_le_moi = float(row["gia_le"])
                gia_buon_moi = float(row["gia_buon"])
                gia_vip_moi = float(row["gia_vip"])
                ton_kho = int(row.get("ton_kho", 0))
                nguong_buon = int(row.get("nguong_buon", 0))

                # Kiểm tra sản phẩm đã tồn tại chưa
                c.execute(
                    "SELECT id, gia_le, gia_buon, gia_vip FROM SanPham WHERE ten=?",
                    (ten,),
                )
                existing = c.fetchone()

                if existing:
                    # Sản phẩm đã tồn tại - cập nhật và lưu lịch sử nếu giá thay đổi
                    sp_id, gia_le_cu, gia_buon_cu, gia_vip_cu = existing

                    # Lưu lịch sử cho từng loại giá nếu thay đổi
                    if user_id:
                        # Giá lẻ
                        if abs(float(gia_le_cu) - gia_le_moi) > 1e-6:
                            c.execute(
                                """
                                INSERT INTO LichSuGia 
                                (sanpham_id, ten_sanpham, loai_gia, gia_cu, gia_moi, user_id, ngay_thay_doi, ghi_chu)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    sp_id,
                                    ten,
                                    "le",
                                    gia_le_cu,
                                    gia_le_moi,
                                    user_id,
                                    ngay_import,
                                    "Import Excel",
                                ),
                            )

                        # Giá buôn
                        if abs(float(gia_buon_cu) - gia_buon_moi) > 1e-6:
                            c.execute(
                                """
                                INSERT INTO LichSuGia 
                                (sanpham_id, ten_sanpham, loai_gia, gia_cu, gia_moi, user_id, ngay_thay_doi, ghi_chu)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    sp_id,
                                    ten,
                                    "buon",
                                    gia_buon_cu,
                                    gia_buon_moi,
                                    user_id,
                                    ngay_import,
                                    "Import Excel",
                                ),
                            )

                        # Giá VIP
                        if abs(float(gia_vip_cu) - gia_vip_moi) > 1e-6:
                            c.execute(
                                """
                                INSERT INTO LichSuGia 
                                (sanpham_id, ten_sanpham, loai_gia, gia_cu, gia_moi, user_id, ngay_thay_doi, ghi_chu)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    sp_id,
                                    ten,
                                    "vip",
                                    gia_vip_cu,
                                    gia_vip_moi,
                                    user_id,
                                    ngay_import,
                                    "Import Excel",
                                ),
                            )

                    # Cập nhật giá và thông tin khác
                    c.execute(
                        """
                        UPDATE SanPham 
                        SET gia_le=?, gia_buon=?, gia_vip=?, ton_kho=?, nguong_buon=?
                        WHERE id=?
                        """,
                        (
                            gia_le_moi,
                            gia_buon_moi,
                            gia_vip_moi,
                            ton_kho,
                            nguong_buon,
                            sp_id,
                        ),
                    )
                else:
                    # Sản phẩm mới - thêm vào database
                    c.execute(
                        """INSERT INTO SanPham (ten, gia_le, gia_buon, gia_vip, ton_kho, nguong_buon)
                        VALUES (?, ?, ?, ?, ?, ?)""",
                        (
                            ten,
                            gia_le_moi,
                            gia_buon_moi,
                            gia_vip_moi,
                            ton_kho,
                            nguong_buon,
                        ),
                    )
        return True
    except Exception as e:
        print("Lỗi import từ DataFrame:", e)
        return False


def xoa_sanpham(ten_sanpham):
    try:
        with db_transaction() as (conn, c):
            c.execute("DELETE FROM SanPham WHERE ten LIKE ?", (ten_sanpham,))
        return True
    except Exception as e:
        print("Lỗi xóa sản phẩm:", e)
        return False
