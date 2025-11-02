import sqlite3

DB_NAME = "fapp.db"


def ket_noi():
    conn = sqlite3.connect(DB_NAME, timeout=30.0)  # Tăng timeout lên 30 giây
    return conn


def khoi_tao_db():
    # Tự động thêm cột ghi_chu vào GiaoDichQuy nếu chưa có
    try:
        conn = ket_noi()
        c = conn.cursor()
        c.execute("PRAGMA table_info(GiaoDichQuy)")
        columns = [row[1] for row in c.fetchall()]
        if "ghi_chu" not in columns:
            c.execute("ALTER TABLE GiaoDichQuy ADD COLUMN ghi_chu TEXT")
            conn.commit()
    except Exception as e:
        print("Lỗi khi thêm cột ghi_chu vào GiaoDichQuy:", e)
    finally:
        conn.close()

    # Tự động thêm cột loai_gia vào LogKho nếu chưa có
    try:
        conn = ket_noi()
        c = conn.cursor()
        c.execute("PRAGMA table_info(LogKho)")
        columns = [row[1] for row in c.fetchall()]
        if "loai_gia" not in columns:
            c.execute("ALTER TABLE LogKho ADD COLUMN loai_gia TEXT")
            conn.commit()
    except Exception as e:
        print("Lỗi khi thêm cột loai_gia vào LogKho:", e)
    finally:
        conn.close()

    # Tự động thêm cột tong_tien, uu_dai, tong_sau_uu_dai, tong_cuoi vào HoaDon nếu chưa có
    try:
        conn = ket_noi()
        c = conn.cursor()
        c.execute("PRAGMA table_info(HoaDon)")
        columns = [row[1] for row in c.fetchall()]
        if "tong_tien" not in columns:
            c.execute("ALTER TABLE HoaDon ADD COLUMN tong_tien REAL DEFAULT 0")
        if "uu_dai" not in columns:
            c.execute("ALTER TABLE HoaDon ADD COLUMN uu_dai REAL DEFAULT 0")
        if "tong_sau_uu_dai" not in columns:
            c.execute("ALTER TABLE HoaDon ADD COLUMN tong_sau_uu_dai REAL DEFAULT 0")
        if "tong_cuoi" not in columns:
            c.execute("ALTER TABLE HoaDon ADD COLUMN tong_cuoi REAL DEFAULT 0")
        conn.commit()
    except Exception as e:
        print("Lỗi khi thêm các cột vào HoaDon:", e)
    finally:
        conn.close()

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
    conn.close()

    # Bảng ghi chênh lệch kiểm kê/nhận hàng để tra cứu sau này
    conn = ket_noi()
    c = conn.cursor()
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

    conn.commit()
    conn.close()


if __name__ == "__main__":
    khoi_tao_db()
    print("DB da duoc khoi tao")
