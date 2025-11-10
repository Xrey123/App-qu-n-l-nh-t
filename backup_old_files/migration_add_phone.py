"""
Migration: Add phone column to Users table

Run this once to add phone support for Zalo notifications
"""

import sqlite3
from utils.logging_config import get_logger

logger = get_logger(__name__)

DB_NAME = "fapp.db"


def add_phone_column():
    """Thêm cột phone vào bảng Users"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        # Check if phone column exists
        c.execute("PRAGMA table_info(Users)")
        columns = [row[1] for row in c.fetchall()]

        if "phone" in columns:
            print("✅ Cột 'phone' đã tồn tại trong bảng Users")
            logger.info("Phone column already exists")
            return True

        # Add phone column
        print("🔧 Thêm cột 'phone' vào bảng Users...")
        c.execute("ALTER TABLE Users ADD COLUMN phone TEXT")
        conn.commit()

        print("✅ Đã thêm cột 'phone' thành công!")
        logger.info("Successfully added phone column to Users table")

        # Show current users
        c.execute("SELECT id, username, phone FROM Users")
        users = c.fetchall()

        print(f"\n📊 Hiện có {len(users)} users:")
        for user_id, username, phone in users:
            phone_str = phone if phone else "Chưa có"
            print(f"   ID {user_id}: {username} - Phone: {phone_str}")

        print("\n💡 Hướng dẫn cập nhật phone:")
        print("   python update_user_phones.py")
        print("   hoặc chạy SQL:")
        print("   UPDATE Users SET phone='84987654321' WHERE username='user1';")

        conn.close()
        return True

    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("✅ Cột 'phone' đã tồn tại")
            return True
        else:
            print(f"❌ Lỗi: {e}")
            logger.error(f"Failed to add phone column: {e}", exc_info=True)
            return False
    except Exception as e:
        print(f"❌ Lỗi không xác định: {e}")
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🔧 MIGRATION: ADD PHONE COLUMN TO USERS")
    print("=" * 60)
    print()

    success = add_phone_column()

    print()
    print("=" * 60)
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
    print("=" * 60)
