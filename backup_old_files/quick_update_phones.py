"""
Quick batch update phone numbers for demo
"""

import sqlite3

# ⚠️ THAY ĐỔI SỐ ĐIỆN THOẠI THẬT CỦA USERS Ở ĐÂY
phone_mapping = {
    "admin": "84912345678",  # ⬅️ Thay số phone thật
    "kt": "84912345678",  # ⬅️ Thay số phone thật
    "giang": "84912345678",  # ⬅️ Thay số phone thật
    "hung": "84912345678",  # ⬅️ Thay số phone thật
    "hội": "84912345678",  # ⬅️ Thay số phone thật
    "dung": "84912345678",  # ⬅️ Thay số phone thật
    "đông": "84912345678",  # ⬅️ Thay số phone thật
}


def quick_update():
    print("=" * 60)
    print("📱 QUICK UPDATE PHONE NUMBERS")
    print("=" * 60)

    conn = sqlite3.connect("fapp.db")
    c = conn.cursor()

    updated = 0
    for username, phone in phone_mapping.items():
        try:
            c.execute("UPDATE Users SET phone=? WHERE username=?", (phone, username))
            conn.commit()
            print(f"✅ {username}: {phone}")
            updated += 1
        except Exception as e:
            print(f"❌ {username}: {e}")

    conn.close()

    print("\n" + "=" * 60)
    print(f"✅ Đã cập nhật {updated}/{len(phone_mapping)} users")
    print("=" * 60)

    # Verify
    print("\n📊 KIỂM TRA KẾT QUẢ:")
    conn = sqlite3.connect("fapp.db")
    c = conn.cursor()
    c.execute("SELECT id, username, phone FROM Users ORDER BY id")

    for user_id, username, phone in c.fetchall():
        status = "✅" if phone else "⚠️"
        print(f"   {status} ID {user_id}: {username:10} -> {phone or 'Chưa có phone'}")

    conn.close()


if __name__ == "__main__":
    quick_update()
