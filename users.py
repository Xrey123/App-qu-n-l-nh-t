from db import ket_noi
import hashlib
from utils.db_helpers import execute_query, execute_update, db_transaction


def lay_username(user_id):
    result = execute_query(
        "SELECT username FROM Users WHERE id=?", (user_id,), fetch_one=True
    )
    return result[0] if result else ""


def ma_hoa_mat_khau(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()


def them_user(username, password, role):
    success = execute_update(
        "INSERT INTO Users (username,password,role) VALUES (?,?,?)",
        (username, ma_hoa_mat_khau(password), role),
    )
    if not success:
        print("Loi them_user")
    return success


def dang_nhap(username, password):
    row = execute_query(
        "SELECT id, role, password FROM Users WHERE username=?",
        (username,),
        fetch_one=True,
    )
    if not row:
        return None
    uid, role, pwd_hash = row
    if ma_hoa_mat_khau(password) == pwd_hash:
        return (uid, role)
    return None


def lay_tat_ca_user():
    return (
        execute_query("SELECT id, username, role, so_du FROM Users", fetch_all=True)
        or []
    )


def xoa_user(user_id):
    success = execute_update("DELETE FROM Users WHERE id=?", (user_id,))
    if not success:
        print("Loi xoa_user")
    return success


def doi_mat_khau(user_id, new_password):
    success = execute_update(
        "UPDATE Users SET password=? WHERE id=?",
        (ma_hoa_mat_khau(new_password), user_id),
    )
    if not success:
        print("Loi doi_mat_khau")
    return success


def lay_so_du(user_id):
    result = execute_query(
        "SELECT so_du FROM Users WHERE id=?", (user_id,), fetch_one=True
    )
    return result[0] if result else 0


def chuyen_tien(tu_user, den_user, so_tien, hoadon_id=None):
    """Chuyển tiền giữa 2 user. Nếu biết hoadon_id, lưu kèm vào giao dịch để theo dõi theo hóa đơn."""
    from datetime import datetime

    # ✅ Validate input
    if so_tien <= 0:
        return False, "Số tiền phải lớn hơn 0"
    if tu_user == den_user and hoadon_id is None:
        return False, "Không thể chuyển tiền cho chính mình"

    try:
        with db_transaction() as (conn, c):
            c.execute("SELECT so_du FROM Users WHERE id=?", (tu_user,))
            r = c.fetchone()
            so_du = r[0] if r else 0
            if so_du < so_tien:
                return False, "Khong du so du"
            c.execute(
                "UPDATE Users SET so_du = so_du - ? WHERE id=?", (so_tien, tu_user)
            )
            c.execute(
                "UPDATE Users SET so_du = so_du + ? WHERE id=?", (so_tien, den_user)
            )
            # Lưu giao dịch với thời gian local (giờ Việt Nam)
            thoi_gian_hien_tai = datetime.now().isoformat()
            if hoadon_id is not None:
                c.execute(
                    "INSERT INTO GiaoDichQuy (user_id, user_nhan_id, so_tien, ngay, hoadon_id) VALUES (?, ?, ?, ?, ?)",
                    (tu_user, den_user, so_tien, thoi_gian_hien_tai, hoadon_id),
                )
            else:
                c.execute(
                    "INSERT INTO GiaoDichQuy (user_id, user_nhan_id, so_tien, ngay) VALUES (?, ?, ?, ?)",
                    (tu_user, den_user, so_tien, thoi_gian_hien_tai),
                )
        return True, None
    except Exception as e:
        return False, str(e)


def lay_tong_nop_theo_hoadon(hoadon_id):
    """Trả về tổng số tiền đã nộp cho một hoadon (theo cột hoadon_id trong GiaoDichQuy)."""
    result = execute_query(
        "SELECT SUM(so_tien) FROM GiaoDichQuy WHERE hoadon_id = ?",
        (hoadon_id,),
        fetch_one=True,
    )
    return result[0] if result and result[0] is not None else 0


def lay_lich_su_quy(user_id=None):
    sql = "SELECT id, user_id, user_nhan_id, so_tien, ngay FROM GiaoDichQuy"
    params = []
    if user_id:
        sql += " WHERE user_id=? OR user_nhan_id=?"
        params = [user_id, user_id]
    return execute_query(sql, tuple(params) if params else None, fetch_all=True) or []


def lay_user_phone(user_id):
    """
    Lấy số điện thoại của user

    Args:
        user_id: ID của user

    Returns:
        Số phone hoặc None nếu không có

    Note: Cần thêm cột phone vào bảng Users trước:
        ALTER TABLE Users ADD COLUMN phone TEXT;
    """
    result = execute_query(
        "SELECT phone FROM Users WHERE id=?", (user_id,), fetch_one=True
    )
    return result[0] if result and result[0] else None


def cap_nhat_user_phone(user_id, phone):
    """
    Cập nhật số điện thoại cho user

    Args:
        user_id: ID của user
        phone: Số điện thoại (format: 84xxxxxxxxx)

    Returns:
        True nếu thành công
    """
    # Validate phone format
    if not phone.startswith("84"):
        return False, "Phone phải bắt đầu bằng 84 (VD: 84987654321)"

    if len(phone) < 11 or len(phone) > 12:
        return False, "Phone không hợp lệ"

    success = execute_update("UPDATE Users SET phone=? WHERE id=?", (phone, user_id))

    if success:
        return True, None
    else:
        return False, "Cập nhật thất bại"


def lay_users_co_no(threshold=-100000):
    """
    Lấy danh sách users đang nợ

    Args:
        threshold: Ngưỡng nợ tối thiểu (VD: -100000 = nợ > 100k)

    Returns:
        List of (user_id, username, phone, so_du)
    """
    result = execute_query(
        "SELECT id, username, phone, so_du FROM Users WHERE so_du < ?",
        (threshold,),
        fetch_all=True,
    )
    return result or []
