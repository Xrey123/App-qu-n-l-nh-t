from db import ket_noi
import hashlib


def ma_hoa_mat_khau(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()


def them_user(username, password, role):
    conn = ket_noi()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO Users (username,password,role) VALUES (?,?,?)",
            (username, ma_hoa_mat_khau(password), role),
        )
        conn.commit()
        return True
    except Exception as e:
        print("Loi them_user:", e)
        return False
    finally:
        conn.close()


def dang_nhap(username, password):
    conn = ket_noi()
    c = conn.cursor()
    try:
        c.execute("SELECT id, role, password FROM Users WHERE username=?", (username,))
        row = c.fetchone()
        if not row:
            return None
        uid, role, pwd_hash = row
        if ma_hoa_mat_khau(password) == pwd_hash:
            return (uid, role)
        return None
    finally:
        conn.close()


def lay_tat_ca_user():
    conn = ket_noi()
    c = conn.cursor()
    c.execute("SELECT id, username, role, so_du FROM Users")
    res = c.fetchall()
    conn.close()
    return res


def xoa_user(user_id):
    conn = ket_noi()
    c = conn.cursor()
    try:
        c.execute("DELETE FROM Users WHERE id=?", (user_id,))
        conn.commit()
        return True
    except Exception as e:
        print("Loi xoa_user:", e)
        return False
    finally:
        conn.close()


def doi_mat_khau(user_id, new_password):
    conn = ket_noi()
    c = conn.cursor()
    try:
        c.execute(
            "UPDATE Users SET password=? WHERE id=?",
            (ma_hoa_mat_khau(new_password), user_id),
        )
        conn.commit()
        return True
    except Exception as e:
        print("Loi doi_mat_khau:", e)
        return False
    finally:
        conn.close()


def lay_so_du(user_id):
    conn = ket_noi()
    c = conn.cursor()
    c.execute("SELECT so_du FROM Users WHERE id=?", (user_id,))
    r = c.fetchone()
    conn.close()
    return r[0] if r else 0


def chuyen_tien(tu_user, den_user, so_tien, hoadon_id=None):
    """Chuyển tiền giữa 2 user. Nếu biết hoadon_id, lưu kèm vào giao dịch để theo dõi theo hóa đơn."""
    conn = ket_noi()
    c = conn.cursor()
    try:
        c.execute("SELECT so_du FROM Users WHERE id=?", (tu_user,))
        r = c.fetchone()
        so_du = r[0] if r else 0
        if so_du < so_tien:
            return False, "Khong du so du"
        c.execute("UPDATE Users SET so_du = so_du - ? WHERE id=?", (so_tien, tu_user))
        c.execute("UPDATE Users SET so_du = so_du + ? WHERE id=?", (so_tien, den_user))
        # Lưu giao dịch có thể kèm hoadon_id (nếu có)
        if hoadon_id is not None:
            c.execute(
                "INSERT INTO GiaoDichQuy (user_id, user_nhan_id, so_tien, ngay, hoadon_id) VALUES (?, ?, ?, datetime('now'), ?)",
                (tu_user, den_user, so_tien, hoadon_id),
            )
        else:
            c.execute(
                "INSERT INTO GiaoDichQuy (user_id, user_nhan_id, so_tien, ngay) VALUES (?, ?, ?, datetime('now'))",
                (tu_user, den_user, so_tien),
            )
        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def lay_tong_nop_theo_hoadon(hoadon_id):
    """Trả về tổng số tiền đã nộp cho một hoadon (theo cột hoadon_id trong GiaoDichQuy)."""
    conn = ket_noi()
    c = conn.cursor()
    try:
        c.execute("SELECT SUM(so_tien) FROM GiaoDichQuy WHERE hoadon_id = ?", (hoadon_id,))
        r = c.fetchone()
        return r[0] if r and r[0] is not None else 0
    finally:
        conn.close()


def lay_lich_su_quy(user_id=None):
    conn = ket_noi()
    c = conn.cursor()
    sql = "SELECT id, user_id, user_nhan_id, so_tien, ngay FROM GiaoDichQuy"
    params = []
    if user_id:
        sql += " WHERE user_id=? OR user_nhan_id=?"
        params = [user_id, user_id]
    c.execute(sql, params)
    res = c.fetchall()
    conn.close()
    return res
