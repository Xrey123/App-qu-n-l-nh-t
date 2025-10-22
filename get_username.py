from db import ket_noi


def lay_username(user_id):
    """Lấy username từ user_id"""
    conn = ket_noi()
    c = conn.cursor()
    try:
        c.execute("SELECT username FROM Users WHERE id=?", (user_id,))
        row = c.fetchone()
        if row:
            return row[0]
        return f"User {user_id}"
    finally:
        conn.close()
