"""
Update User Phone Numbers

Interactive script to update phone numbers for all users
"""

from users import lay_tat_ca_user, cap_nhat_user_phone
from utils.logging_config import get_logger

logger = get_logger(__name__)


def update_phones_interactive():
    """Cập nhật phone cho từng user"""
    users = lay_tat_ca_user()

    print("=" * 60)
    print("📱 CẬP NHẬT SỐ ĐIỆN THOẠI CHO USERS")
    print("=" * 60)
    print()

    for user_id, username, role, so_du in users:
        print(f"\n👤 User: {username} (ID: {user_id})")
        print(f"   Vai trò: {role}")
        print(f"   Số dư: {so_du:,.0f} VNĐ")

        phone = input("   Nhập số phone (84xxxxxxxxx) hoặc Enter để bỏ qua: ").strip()

        if not phone:
            print("   ⏭️  Bỏ qua")
            continue

        # Validate và cập nhật
        success, error = cap_nhat_user_phone(user_id, phone)

        if success:
            print(f"   ✅ Đã cập nhật phone: {phone}")
            logger.info(f"Updated phone for user {username}: {phone}")
        else:
            print(f"   ❌ Lỗi: {error}")
            logger.error(f"Failed to update phone for user {username}: {error}")

    print("\n" + "=" * 60)
    print("✅ HOÀN TẤT CẬP NHẬT")
    print("=" * 60)


def update_phones_from_dict():
    """Cập nhật phone từ dict (nếu biết trước)"""
    # TODO: Thay đổi phone numbers ở đây
    phone_mapping = {
        "admin": "84987654321",
        "user1": "84912345678",
        "user2": "84901234567",
        # Thêm users khác...
    }

    print("=" * 60)
    print("📱 CẬP NHẬT PHONE TỪ DANH SÁCH")
    print("=" * 60)
    print()

    users = lay_tat_ca_user()
    updated = 0
    failed = 0

    for user_id, username, role, so_du in users:
        if username in phone_mapping:
            phone = phone_mapping[username]
            success, error = cap_nhat_user_phone(user_id, phone)

            if success:
                print(f"✅ {username}: {phone}")
                updated += 1
            else:
                print(f"❌ {username}: {error}")
                failed += 1
        else:
            print(f"⏭️  {username}: Không có trong danh sách")

    print()
    print(f"Kết quả: {updated} thành công, {failed} thất bại")


if __name__ == "__main__":
    import sys

    print("\nChọn phương thức:")
    print("1. Nhập từng user (interactive)")
    print("2. Cập nhật từ danh sách trong code")

    choice = input("\nChọn (1/2): ").strip()

    if choice == "1":
        update_phones_interactive()
    elif choice == "2":
        print("\n⚠️  Vui lòng sửa phone_mapping trong code trước!")
        print("   Mở file: update_user_phones.py")
        print("   Tìm: phone_mapping = {...}")
        print("   Sửa phone numbers cho users")
        print()
        confirm = input("Đã sửa xong? (y/n): ").strip().lower()
        if confirm == "y":
            update_phones_from_dict()
        else:
            print("❌ Hủy bỏ")
    else:
        print("❌ Lựa chọn không hợp lệ")
