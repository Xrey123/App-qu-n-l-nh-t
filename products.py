from db import ket_noi
import pandas as pd


def them_sanpham(ten, gia_le, gia_buon, gia_vip, ton_kho=0, nguong_buon=0):
    # ✅ Validate input
    if gia_le < 0 or gia_buon < 0 or gia_vip < 0:
        print("Lỗi: Giá không được âm")
        return False
    if ton_kho < 0 or nguong_buon < 0:
        print("Lỗi: Số lượng không được âm")
        return False
    
    conn = ket_noi()
    c = conn.cursor()
    try:
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
        conn.commit()
        return True
    except Exception as e:
        print("Lỗi thêm sản phẩm:", e)
        conn.rollback()
        return False
    finally:
        conn.close()


def cap_nhat_ton(product_id, ton_moi):
    # ✅ Validate input
    if ton_moi < 0:
        print("Lỗi: Tồn kho không được âm")
        return False
    
    conn = ket_noi()
    c = conn.cursor()
    try:
        c.execute("UPDATE SanPham SET ton_kho=? WHERE id=?", (ton_moi, product_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Lỗi cập nhật tồn kho: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def tim_sanpham(keyword):
    conn = ket_noi()
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM SanPham WHERE ten LIKE ?", ("%" + keyword + "%",))
        res = c.fetchall()
        return res
    finally:
        conn.close()


def lay_tat_ca_sanpham():
    conn = ket_noi()
    c = conn.cursor()
    try:
        c.execute(
            "SELECT id, ten, gia_le, gia_buon, gia_vip, ton_kho, nguong_buon FROM SanPham"
        )
        data = c.fetchall()
        return data
    finally:
        conn.close()


def lay_danh_sach_ten_sanpham():
    conn = ket_noi()
    c = conn.cursor()
    try:
        c.execute("SELECT ten FROM SanPham")
        ten_sanpham = [row[0] for row in c.fetchall()]
        return ten_sanpham
    except Exception as e:
        return []
    finally:
        conn.close()


def import_sanpham_from_dataframe(df):
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

    conn = ket_noi()
    c = conn.cursor()
    try:
        c.execute("DELETE FROM SanPham")
        c.execute("DELETE FROM sqlite_sequence WHERE name='SanPham'")
        for _, row in df.iterrows():
            ten = row["ten"]
            gia_le = float(row["gia_le"])
            gia_buon = float(row["gia_buon"])
            gia_vip = float(row["gia_vip"])
            ton_kho = int(row.get("ton_kho", 0))
            nguong_buon = int(row.get("nguong_buon", 0))
            c.execute(
                """INSERT INTO SanPham (ten, gia_le, gia_buon, gia_vip, ton_kho, nguong_buon)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (ten, gia_le, gia_buon, gia_vip, ton_kho, nguong_buon),
            )
        conn.commit()
        return True
    except Exception as e:
        print("Lỗi import từ DataFrame:", e)
        return False
    finally:
        conn.close()


def xoa_sanpham(ten_sanpham):
    conn = ket_noi()
    c = conn.cursor()
    try:
        c.execute("DELETE FROM SanPham WHERE ten LIKE ?", (ten_sanpham,))
        conn.commit()
        return True
    except Exception as e:
        print("Lỗi xóa sản phẩm:", e)
        return False
    finally:
        conn.close()
