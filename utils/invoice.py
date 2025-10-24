# Helpers for invoice-related calculations

def tinh_unpaid_total(chi_tiet_rows):
    """
    Compute unpaid total for an invoice detail list.
    Expects rows with indices:
      [.., so_luong(4), loai_gia(5), gia(6), xuat_hoa_don(7), gia_le(8), giam(9), ...]
    Only counts rows where xuat_hoa_don == 0.
    Formula: so_luong * gia - giam
    """
    if not chi_tiet_rows:
        return 0
    total = 0
    for row in chi_tiet_rows:
        try:
            if len(row) > 9 and row[7] == 0:
                so_luong = float(row[4])
                gia = float(row[6])
                giam = float(row[9])
                total += so_luong * gia - giam
        except Exception:
            # Skip malformed rows but continue
            continue
    return total


def xac_dinh_loai_gia(so_luong, nguong_buon, is_vip):
    """Xác định loại giá: 'vip', 'buon' hoặc 'le'.

    - Nếu is_vip: 'vip'
    - Ngược lại nếu so_luong >= nguong_buon: 'buon'
    - Ngược lại: 'le'
    """
    try:
        sl = float(so_luong)
    except Exception:
        sl = 0.0
    try:
        nguong = float(nguong_buon) if nguong_buon is not None else 0.0
    except Exception:
        nguong = 0.0

    if is_vip:
        return "vip"
    if sl >= nguong:
        return "buon"
    return "le"


def chon_don_gia(sp_row, so_luong, is_vip):
    """Chọn đơn giá từ một bản ghi sản phẩm theo SL và VIP.

    sp_row: (id, ten, gia_le, gia_buon, gia_vip, ton_kho, nguong_buon)
    Trả về đơn giá float.
    """
    try:
        loai = xac_dinh_loai_gia(
            so_luong, sp_row[6] if len(sp_row) > 6 else 0, is_vip
        )
        if loai == "vip":
            return float(sp_row[4])
        if loai == "buon":
            return float(sp_row[3])
        return float(sp_row[2])
    except Exception:
        # Fallback an toàn
        try:
            return float(sp_row[2])
        except Exception:
            return 0.0


def tinh_chenh_lech(loai_gia, xhd, so_luong, gia_le, giam, gia_buon=None):
    """Tính chênh lệch theo quy tắc hiện tại.

    Quy tắc:
    - Nếu xhd == 1: 0
    - Nếu loai_gia in ('vip', 'buon'): 0
    - Nếu loai_gia == 'le': (gia_le - gia_buon) * so_luong - giam (nếu có gia_buon)
    - Nếu thiếu gia_buon: 0
    Giá trị đầu vào có thể là str/float; sẽ được chuyển về float an toàn.
    """
    try:
        if int(xhd) == 1:
            return 0.0
    except Exception:
        # Nếu xhd không parse được, coi như chưa xuất
        pass

    lg = str(loai_gia).lower() if loai_gia is not None else ""
    if lg in ("vip", "buon"):
        return 0.0

    if lg == "le":
        try:
            sl = float(so_luong or 0)
        except Exception:
            sl = 0.0
        try:
            gl = float(gia_le or 0)
        except Exception:
            gl = 0.0
        try:
            g = float(giam or 0)
        except Exception:
            g = 0.0
        if gia_buon is None:
            return 0.0
        try:
            gb = float(gia_buon)
        except Exception:
            return 0.0
        return gl * sl - gb * sl - g

    return 0.0
