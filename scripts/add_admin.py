from users import them_user, ma_hoa_mat_khau
from db import khoi_tao_db


def add_admin():
    khoi_tao_db()
    username = "admin"
    password = "admin123"
    role = "admin"
    if them_user(username, password, role):
        print(f"Đã thêm user '{username}' với role '{role}' thành công!")
    else:
        print(f"Thêm user '{username}' thất bại, có thể username đã tồn tại.")


if __name__ == "__main__":
    add_admin()
