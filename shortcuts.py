"""
SHORTCUTS.PY - Danh sách tên gọi tắt sản phẩm
Bạn có thể thêm tên gọi tắt mới vào đây
"""

# DANH SÁCH TÊN GỌI TẮT
PRODUCT_SHORTCUTS = {
    # ============ VIẾT TẮT THEO MÃ ============
    "2t": ["racer 2t", "2t"],
    "sf": ["racer sf"],
    "sj": ["racer sj"],
    "scooter": ["racer scooter"],
    # ============ GỌI THEO THÔNG SỐ NHỚT ============
    "nhot 40": ["20w/40", "20w40", "shd/40", "shd 40"],
    "nhot 50": ["20w/50", "20w50", "shd/50", "shd 50"],
    "nhot 15w40": ["15w/40", "15w40", "ci-4 15w/40"],
    "40": ["20w/40", "shd/40", "shd 40"],
    "50": ["20w/50", "shd/50", "shd 50"],
    # ============ GỌI THEO DUNG TÍCH ============
    "200 lit": ["200 lít", "200lit"],
    "18 lit": ["18 lít", "18lit"],
    "25 lit": ["25 lít", "25lit"],
    "4 lit": ["4 lít", "4lit"],
    "1 lit": ["1 lít", "1lit"],
    "200l": ["200 lít"],
    "18l": ["18 lít"],
    "25l": ["25 lít"],
    "4l": ["4 lít"],
    "1l": ["1 lít"],
    # ============ GỌI THEO DÒNG SẢN PHẨM ============
    "super": ["komat super"],
    "shd": ["komat shd"],
    "racer": ["plc racer"],
    "komat": ["plc komat"],
    "carter": ["plc carter"],
    "cacer": ["plc cacer"],
    "gear": ["gear oil"],
    "hydro": ["hydroil"],
    "hydroil": ["hydroil"],
    # ============ COMBO THÔNG DỤNG ============
    "nhot super 40": ["komat super 20w/40"],
    "nhot super 50": ["komat super 20w/50"],
    "nhot racer": ["plc racer"],
    "dau nhot 40": ["20w/40", "shd/40"],
    "dau nhot 50": ["20w/50", "shd/50"],
    "super 40": ["komat super 20w/40"],
    "super 50": ["komat super 20w/50"],
    # ============ THÊM TÊN CỦA BẠN Ở ĐÂY ============
    # Ví dụ:
    # "ten_tat": ["tu_khoa_1", "tu_khoa_2"],
    # "xe may": ["racer scooter"],
    # "thung lon": ["200 lít"],
}


def get_shortcuts():
    """Lấy danh sách shortcuts"""
    return PRODUCT_SHORTCUTS


def add_shortcut(name, keywords):
    """
    Thêm tên gọi tắt mới

    Args:
        name (str): Tên gọi tắt (vd: "nhot xe")
        keywords (list): Danh sách từ khóa mở rộng (vd: ["racer scooter"])
    """
    PRODUCT_SHORTCUTS[name.lower()] = keywords
    print(f"✅ Đã thêm: '{name}' → {keywords}")


def list_shortcuts():
    """Hiển thị tất cả shortcuts"""
    print("📋 DANH SÁCH TÊN GỌI TẮT:\n")

    for shortcut, expansions in PRODUCT_SHORTCUTS.items():
        print(f"  '{shortcut}' → {', '.join(expansions)}")


if __name__ == "__main__":
    print("=" * 70)
    print("🏷️ DANH SÁCH TÊN GỌI TẮT SẢN PHẨM".center(70))
    print("=" * 70)
    print()

    list_shortcuts()

    print()
    print("─" * 70)
    print(f"📊 Tổng: {len(PRODUCT_SHORTCUTS)} tên gọi tắt")
    print("─" * 70)
    print()
    print("💡 CÁCH THÊM MỚI:")
    print("   1. Mở file shortcuts.py")
    print("   2. Thêm vào phần '# THÊM TÊN CỦA BẠN Ở ĐÂY'")
    print('   3. Format: "ten_tat": ["tu_khoa_1", "tu_khoa_2"],')
    print()
    print("📖 VÍ DỤ:")
    print('   "xe may": ["racer scooter"],')
    print('   "thung lon": ["200 lít"],')
    print('   "nhot xe": ["racer", "scooter"],')
