import sqlite3
import hashlib
from utils.logging_config import get_logger

logger = get_logger(__name__)

DB_NAME = "fapp.db"


def ket_noi():
    """Get database connection. Consider using get_db_connection() context manager instead."""
    conn = sqlite3.connect(DB_NAME, timeout=30.0)
    return conn


def _add_column_if_missing(table_name: str, column_name: str, column_def: str):
    """Helper to safely add column to table if it doesn't exist."""
    try:
        conn = ket_noi()
        c = conn.cursor()

        c.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        )
        if not c.fetchone():
            logger.warning(
                f"Bo qua thêm cột '{column_name}' vì bảng {table_name} chưa được tạo."
            )
            return

        c.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in c.fetchall()]

        if column_name not in columns:
            logger.info(f"Adding column '{column_name}' to {table_name}...")
            c.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_def}")
            conn.commit()
            logger.info(f"Successfully added column '{column_name}' to {table_name}")
        else:
            logger.debug(f"Column '{column_name}' already exists in {table_name}")
    except sqlite3.OperationalError as e:
        logger.error(f"Failed to add column '{column_name}' to {table_name}: {e}")
        raise
    except sqlite3.DatabaseError as e:
        logger.error(
            f"Database error while adding column to {table_name}: {e}", exc_info=True
        )
        raise
    finally:
        try:
            conn.close()
        except:
            pass


def khoi_tao_db():
    conn = ket_noi()
    c = conn.cursor()

    # Bang Users (đã có so_du cho sổ quỹ)
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            so_du REAL DEFAULT 0
        )
    """
    )

    # Bang SanPham (cập nhật nguong_buon nếu cần)
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS SanPham (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ten TEXT UNIQUE NOT NULL,
            gia_le REAL NOT NULL,
            gia_buon REAL NOT NULL,
            gia_vip REAL NOT NULL,
            ton_kho REAL DEFAULT 0,
            nguong_buon INTEGER DEFAULT 0
        )
    """
    )

    # Bang HoaDon (thêm giam_gia, khach_uu_dai, xuat_hoa_don)
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS HoaDon (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            khach_hang TEXT,
            ngay TEXT,
            trang_thai TEXT,
            tong REAL,
            giam_gia REAL DEFAULT 0,
            khach_uu_dai INTEGER DEFAULT 0,
            xuat_hoa_don INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES Users(id)
        )
    """
    )

    # Bang ChiTietHoaDon (thêm xuat_hoa_don, loai_gia, ghi_chu)
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS ChiTietHoaDon (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hoadon_id INTEGER,
            sanpham_id INTEGER,
            so_luong REAL,
            gia REAL,
            loai_gia TEXT,
            giam REAL DEFAULT 0,
            xuat_hoa_don INTEGER DEFAULT 0,
            ghi_chu TEXT DEFAULT '',
            FOREIGN KEY(hoadon_id) REFERENCES HoaDon(id),
            FOREIGN KEY(sanpham_id) REFERENCES SanPham(id)
        )
    """
    )

    # Bang LogKho
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS LogKho (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sanpham_id INTEGER,
            user_id INTEGER,
            ngay TEXT,
            hanh_dong TEXT,
            so_luong REAL,
            ton_truoc REAL,
            ton_sau REAL,
            gia_ap_dung REAL,
            chenh_lech_cong_doan REAL DEFAULT 0,
            loai_gia TEXT,
            FOREIGN KEY(sanpham_id) REFERENCES SanPham(id),
            FOREIGN KEY(user_id) REFERENCES Users(id)
        )
    """
    )

    # Bang CongDoan (cho công đoàn)
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS CongDoan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sanpham_id INTEGER,
            user_id INTEGER,
            ngay TEXT,
            so_luong INTEGER,
            chenh_lech REAL,
            FOREIGN KEY(sanpham_id) REFERENCES SanPham(id),
            FOREIGN KEY(user_id) REFERENCES Users(id)
        )
    """
    )

    # Bang GiaoDichQuy (cho sổ quỹ)
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS GiaoDichQuy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,          -- ai thực hiện chuyển tiền
            user_nhan_id INTEGER,     -- ai nhận tiền
            so_tien REAL,
            ngay TEXT
        )
    """
    )

    # Thử thêm cột hoadon_id nếu DB cũ chưa có (ALTER TABLE ADD COLUMN an toàn trong sqlite)
    try:
        c.execute("ALTER TABLE GiaoDichQuy ADD COLUMN hoadon_id INTEGER")
    except Exception:
        # Nếu cột đã tồn tại hoặc lệnh thất bại, bỏ qua
        pass

    conn.commit()

    # Bảng ghi chênh lệch kiểm kê/nhận hàng để tra cứu sau này
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS ChenhLech (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sanpham_id INTEGER,
            user_id INTEGER,
            ngay TEXT,
            chenh REAL,
            ton_truoc REAL,
            ton_sau REAL,
            ghi_chu TEXT,
            FOREIGN KEY(sanpham_id) REFERENCES SanPham(id),
            FOREIGN KEY(user_id) REFERENCES Users(id)
        )
        """
    )

    # Bảng đầu kỳ xuất bỏ (để theo dõi số lượng có thể xuất theo từng loại giá)
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS DauKyXuatBo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            sanpham_id INTEGER,
            ten_sanpham TEXT,
            so_luong REAL,
            loai_gia TEXT,
            gia REAL,
            ngay TEXT,
            FOREIGN KEY(user_id) REFERENCES Users(id),
            FOREIGN KEY(sanpham_id) REFERENCES SanPham(id)
        )
        """
    )

    # Bảng xuất dư (để theo dõi số lượng xuất vượt quá số lượng bán)
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS XuatDu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            sanpham_id INTEGER,
            ten_sanpham TEXT,
            so_luong REAL,
            loai_gia TEXT,
            ngay TEXT,
            FOREIGN KEY(user_id) REFERENCES Users(id),
            FOREIGN KEY(sanpham_id) REFERENCES SanPham(id)
        )
        """
    )

    # Bảng chênh lệch xuất bổ (để theo dõi chênh lệch khi xuất bổ)
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS ChenhLechXuatBo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            sanpham_id INTEGER,
            ten_sanpham TEXT,
            so_luong REAL,
            loai_gia_nguon TEXT,
            loai_gia_xuat TEXT,
            gia_ban REAL,
            gia_xuat REAL,
            chenh_lech REAL,
            ngay TEXT,
            FOREIGN KEY(user_id) REFERENCES Users(id),
            FOREIGN KEY(sanpham_id) REFERENCES SanPham(id)
        )
        """
    )

    # Bổ sung cột phân loại giá mới/cũ nếu chưa có
    try:
        c.execute("PRAGMA table_info(ChenhLechXuatBo)")
        cols = [row[1] for row in c.fetchall()]
        if "is_gia_moi" not in cols:
            c.execute("ALTER TABLE ChenhLechXuatBo ADD COLUMN is_gia_moi INTEGER")
    except Exception:
        pass

    # Bảng lịch sử thay đổi giá sản phẩm
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS LichSuGia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sanpham_id INTEGER,
            ten_sanpham TEXT,
            loai_gia TEXT,
            gia_cu REAL,
            gia_moi REAL,
            user_id INTEGER,
            ngay_thay_doi TEXT,
            ghi_chu TEXT,
            FOREIGN KEY(sanpham_id) REFERENCES SanPham(id),
            FOREIGN KEY(user_id) REFERENCES Users(id)
        )
        """
    )

    # Bảng feedback AI (Like/Dislike)
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS AI_Feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            conversation_id TEXT,
            question TEXT,
            answer TEXT,
            is_helpful INTEGER,
            timestamp TEXT,
            FOREIGN KEY(user_id) REFERENCES Users(id)
        )
        """
    )

    conn.commit()
    conn.close()

    # Bổ sung các cột thiếu sau khi bảo đảm bảng đã tồn tại
    _add_column_if_missing("SanPham", "don_vi", "don_vi TEXT DEFAULT ''")
    _add_column_if_missing("GiaoDichQuy", "ghi_chu", "ghi_chu TEXT")
    _add_column_if_missing("LogKho", "loai_gia", "loai_gia TEXT")

    for col_name, col_def in [
        ("tong_tien", "tong_tien REAL DEFAULT 0"),
        ("uu_dai", "uu_dai REAL DEFAULT 0"),
        ("tong_sau_uu_dai", "tong_sau_uu_dai REAL DEFAULT 0"),
        ("tong_cuoi", "tong_cuoi REAL DEFAULT 0"),
    ]:
        _add_column_if_missing("HoaDon", col_name, col_def)

    # Khởi tạo user mặc định nếu bảng Users đang rỗng
    try:
        conn = ket_noi()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM Users")
        count = c.fetchone()[0]
        if count == 0:
            default_username = "admin"
            default_password = "admin123"
            hashed_password = hashlib.sha256(default_password.encode()).hexdigest()
            c.execute(
                "INSERT INTO Users (username, password, role) VALUES (?, ?, ?)",
                (default_username, hashed_password, "admin"),
            )
            conn.commit()
            logger.info(
                "Da tao user mac dinh 'admin' (mat khau: admin123). Vui long doi mat khau sau khi dang nhap."
            )
    except sqlite3.Error as e:
        logger.error("Khong the khoi tao user mac dinh: %s", e, exc_info=True)
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    khoi_tao_db()
    print("DB da duoc khoi tao")
