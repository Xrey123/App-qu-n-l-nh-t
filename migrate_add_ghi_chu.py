# -*- coding: utf-8 -*-
import sqlite3
import sys
import io
from db import ket_noi

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def migrate_add_ghi_chu():
    """Them cot ghi_chu vao bang ChiTietHoaDon"""
    conn = ket_noi()
    c = conn.cursor()

    try:
        # Kiem tra xem cot ghi_chu da ton tai chua
        c.execute("PRAGMA table_info(ChiTietHoaDon)")
        columns = [col[1] for col in c.fetchall()]

        if 'ghi_chu' not in columns:
            print("Adding ghi_chu column to ChiTietHoaDon...")
            c.execute("ALTER TABLE ChiTietHoaDon ADD COLUMN ghi_chu TEXT DEFAULT ''")
            conn.commit()
            print("Added ghi_chu column successfully!")
        else:
            print("Column ghi_chu already exists.")

    except Exception as e:
        print(f"Migration error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_add_ghi_chu()
