from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDateEdit, QPushButton, 
    QTableWidget, QTableWidgetItem
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor, QFont
from gui.utils import setup_table
from utils.ui_helpers import show_error
from db import ket_noi

class HomeTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
        # Auto-load on init (with error handling)
        try:
            self.load_home_data()
        except Exception as e:
            print(f"⚠️ Tab Home init: Không thể tải dữ liệu ban đầu - {e}")

    def init_ui(self):
        """Tab Home - Tổng quan sản phẩm đã xuất (XHD + Xuất bổ) với quy đổi LÍT"""
        layout = QVBoxLayout()

        # Title
        title = QLabel("<h2>🏠 TỔNG QUAN SẢN PHẨM ĐÃ XUẤT</h2>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Filter bar
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Từ ngày:"))
        self.home_tu_ngay = QDateEdit()
        self.home_tu_ngay.setCalendarPopup(True)
        self.home_tu_ngay.setDate(QDate.currentDate().addMonths(-1))
        filter_layout.addWidget(self.home_tu_ngay)

        filter_layout.addWidget(QLabel("Đến ngày:"))
        self.home_den_ngay = QDateEdit()
        self.home_den_ngay.setCalendarPopup(True)
        self.home_den_ngay.setDate(QDate.currentDate())
        filter_layout.addWidget(self.home_den_ngay)

        btn_load_home = QPushButton("📊 Tải dữ liệu")
        btn_load_home.clicked.connect(self.load_home_data)
        filter_layout.addWidget(btn_load_home)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Table
        self.tbl_home = QTableWidget()
        self.tbl_home.setColumnCount(6)
        self.tbl_home.setHorizontalHeaderLabels(
            [
                "Tên sản phẩm",
                "Đơn vị",
                "Tồn kho",
                "Đã xuất (XHD)",
                "Đã xuất (Xuất bổ)",
                "Tổng LÍT",
            ]
        )
        setup_table(self.tbl_home)
        layout.addWidget(self.tbl_home)

        # Summary labels
        summary_layout = QHBoxLayout()
        self.lbl_home_tong_sp = QLabel("Tổng sản phẩm: 0")
        self.lbl_home_tong_lit = QLabel("Tổng LÍT đã xuất: 0")
        summary_layout.addWidget(self.lbl_home_tong_sp)
        summary_layout.addStretch()
        summary_layout.addWidget(self.lbl_home_tong_lit)
        layout.addLayout(summary_layout)

        self.setLayout(layout)

    def parse_don_vi_to_liters(self, don_vi_text):
        """
        Parse đơn vị thành số LÍT

        ⚠️ QUY TẮC ĐặC BIỆT:
        - Nếu parse ra >= 50 lít → Coi như 1 đơn vị = 1 lít
        - Nếu parse ra < 50 lít → Giữ nguyên giá trị

        Ví dụ:
        - "209 lít" → Parse: 209 → Vì 209 >= 50 → Return: 1 lít/đơn vị
        - "4 lít" → Parse: 4 → Vì 4 < 50 → Return: 4 lít/đơn vị
        - "1 lít" → 1
        - "lít" → 1
        - "chai" / "lon" / khác → 1 (mặc định)

        Returns:
            float: Số lít per đơn vị
        """
        if not don_vi_text:
            return 1.0

        import re

        text = str(don_vi_text).lower().strip()

        # Pattern: "209 lít", "4 lít", etc
        match = re.search(r"(\d+(?:\.\d+)?)\s*l[ií]t", text)
        if match:
            parsed_value = float(match.group(1))

            # ⚠️ QUY TẮC ĐẶC BIỆT: Nếu >= 50 → Chỉ tính 1 lít/đơn vị
            if parsed_value >= 50:
                return 1.0
            else:
                return parsed_value

        # Nếu chỉ có "lít" (không có số)
        if "lít" in text or "lit" in text:
            return 1.0

        # Mặc định: 1 đơn vị = 1 lít
        return 1.0

    def load_home_data(self):
        """Load dữ liệu tổng quan: Tồn kho + Đã xuất (XHD + Xuất bổ)"""
        try:
            tu_ngay = self.home_tu_ngay.date().toString("yyyy-MM-dd")
            den_ngay = self.home_den_ngay.date().toString("yyyy-MM-dd")

            conn = ket_noi()
            c = conn.cursor()

            # Lấy tất cả sản phẩm
            c.execute(
                """
                SELECT id, ten, don_vi, 
                       COALESCE(gia_le, 0), 
                       COALESCE(gia_buon, 0), 
                       COALESCE(gia_vip, 0)
                FROM SanPham
                ORDER BY ten
            """
            )
            products = c.fetchall()

            data = []
            tong_lit = 0.0

            for product in products:
                product_id = product[0]
                ten = product[1]
                don_vi = product[2]

                # Parse đơn vị → số lít
                liters_per_unit = self.parse_don_vi_to_liters(don_vi)

                # 1. Tồn kho
                c.execute(
                    """
                    SELECT COALESCE(SUM(so_luong), 0)
                    FROM LogKho
                    WHERE sanpham_id = ?
                """,
                    (product_id,),
                )
                ton_kho_result = c.fetchone()
                ton_kho = ton_kho_result[0] if ton_kho_result else 0

                # 2. Đã xuất HÓA ĐƠN (XHD = 1)
                c.execute(
                    """
                    SELECT COALESCE(SUM(ct.so_luong), 0)
                    FROM ChiTietHoaDon ct
                    JOIN HoaDon h ON ct.hoadon_id = h.id
                    JOIN SanPham s ON ct.sanpham_id = s.id
                    WHERE s.id = ?
                      AND ct.xuat_hoa_don = 1
                      AND date(h.ngay) >= ?
                      AND date(h.ngay) <= ?
                """,
                    (product_id, tu_ngay, den_ngay),
                )
                xhd_result = c.fetchone()
                xhd_qty = xhd_result[0] if xhd_result else 0

                # 3. Đã xuất BỔ (từ bảng ChenhLechXuatBo)
                c.execute(
                    """
                    SELECT COALESCE(SUM(so_luong), 0)
                    FROM ChenhLechXuatBo
                    WHERE ten_sanpham = ?
                      AND date(ngay) >= ?
                      AND date(ngay) <= ?
                """,
                    (ten, tu_ngay, den_ngay),
                )
                xuat_bo_result = c.fetchone()
                xuat_bo_qty = xuat_bo_result[0] if xuat_bo_result else 0

                # Tính tổng LÍT
                total_qty = float(xhd_qty) + float(xuat_bo_qty)
                total_liters = total_qty * liters_per_unit

                # Chỉ hiển thị sản phẩm có xuất
                if total_qty > 0:
                    data.append(
                        {
                            "ten": ten,
                            "don_vi": don_vi,
                            "ton_kho": ton_kho,
                            "xhd": xhd_qty,
                            "xuat_bo": xuat_bo_qty,
                            "liters": total_liters,
                        }
                    )
                    tong_lit += total_liters

            conn.close()

            # Hiển thị lên bảng
            self.tbl_home.setRowCount(len(data))

            for row, item in enumerate(data):
                # Tên sản phẩm
                self.tbl_home.setItem(row, 0, QTableWidgetItem(item["ten"]))

                # Đơn vị
                self.tbl_home.setItem(row, 1, QTableWidgetItem(item["don_vi"]))

                # Tồn kho
                self.tbl_home.setItem(
                    row, 2, QTableWidgetItem(f"{item['ton_kho']:.2f}")
                )

                # Đã xuất XHD
                self.tbl_home.setItem(row, 3, QTableWidgetItem(f"{item['xhd']:.2f}"))

                # Đã xuất Xuất bổ
                self.tbl_home.setItem(
                    row, 4, QTableWidgetItem(f"{item['xuat_bo']:.2f}")
                )

                # Tổng LÍT
                lit_item = QTableWidgetItem(f"{item['liters']:.2f} L")
                lit_item.setForeground(QColor(0, 100, 200))  # Màu xanh dương
                
                font = QFont()
                font.setBold(True)
                lit_item.setFont(font)
                self.tbl_home.setItem(row, 5, lit_item)

            # Update summary
            self.lbl_home_tong_sp.setText(f"Tổng sản phẩm: {len(data)}")
            self.lbl_home_tong_lit.setText(
                f"<b>Tổng LÍT đã xuất: {tong_lit:,.2f} L</b>"
            )

            # Resize columns
            self.tbl_home.resizeColumnsToContents()

        except Exception as e:
            show_error(self, "Lỗi", f"Lỗi tải dữ liệu Home: {e}")
            import traceback
            traceback.print_exc()
