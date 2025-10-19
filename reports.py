from db import ket_noi


def bao_cao_kho():
    conn = ket_noi()
    c = conn.cursor()
    c.execute(
        """
        SELECT s.id, s.ten, s.ton_kho,
               (SELECT SUM(so_luong) FROM ChiTietHoaDon WHERE sanpham_id=s.id) as da_ban,
               (SELECT SUM(so_luong) FROM LogKho WHERE sanpham_id=s.id AND hanh_dong='xuat_bo') as xuat_bo
        FROM SanPham s
    """
    )
    res = c.fetchall()
    conn.close()
    return res


def bao_cao_doanh_thu():
    conn = ket_noi()
    c = conn.cursor()
    c.execute("SELECT SUM(tong) FROM HoaDon WHERE trang_thai='Da_xuat'")
    res = c.fetchone()[0] or 0
    conn.close()
    return res


def chi_tiet_log_kho(sanpham_id=None, tu_ngay=None, den_ngay=None):
    conn = ket_noi()
    c = conn.cursor()
    sql = "SELECT id, sanpham_id, user_id, ngay, hanh_dong, so_luong, ton_truoc, ton_sau FROM LogKho WHERE 1=1"
    params = []
    if sanpham_id:
        sql += " AND sanpham_id=?"
        params.append(sanpham_id)
    if tu_ngay:
        sql += " AND date(ngay) >= date(?)"
        params.append(tu_ngay)
    if den_ngay:
        sql += " AND date(ngay) <= date(?)"
        params.append(den_ngay)
    sql += " ORDER BY ngay DESC"
    c.execute(sql, params)
    res = c.fetchall()
    conn.close()
    return res


def doanh_thu_theo_thang(nam, thang):
    conn = ket_noi()
    c = conn.cursor()
    like = f"{nam:04d}-{thang:02d}-%"
    c.execute(
        "SELECT IFNULL(SUM(tong),0) FROM HoaDon WHERE trang_thai='Da_xuat' AND ngay LIKE ?",
        (like,),
    )
    r = c.fetchone()[0] or 0
    conn.close()
    return r


def bao_cao_xuat_theo_thang(nam, thang):
    conn = ket_noi()
    c = conn.cursor()
    like = f"{nam:04d}-{thang:02d}-%"
    c.execute(
        """
        SELECT s.ten, SUM(ct.so_luong) as tong_sl
        FROM ChiTietHoaDon ct JOIN SanPham s ON ct.sanpham_id = s.id
        JOIN HoaDon hd ON ct.hoadon_id = hd.id
        WHERE hd.trang_thai = 'Da_xuat' AND hd.ngay LIKE ?
        GROUP BY s.ten
    """,
        (like,),
    )
    res = c.fetchall()
    c.execute(
        """
        SELECT s.ten, SUM(lk.so_luong) as tong_sl
        FROM LogKho lk JOIN SanPham s ON lk.sanpham_id = s.id
        WHERE lk.hanh_dong = 'xuat_bo' AND lk.ngay LIKE ?
        GROUP BY s.ten
    """,
        (like,),
    )
    xuat_bo = c.fetchall()
    conn.close()

    # Gom tổng
    tong = {}
    for ten, sl in res + xuat_bo:
        tong[ten] = tong.get(ten, 0) + sl
    return list(tong.items())
