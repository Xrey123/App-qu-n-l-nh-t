from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QPushButton, 
    QTableWidgetItem, QLineEdit, QDoubleSpinBox, QComboBox, QHeaderView,
    QMessageBox, QDialog
)
from PyQt5.QtCore import Qt
from gui.utils import setup_table, format_price
from utils.ui_helpers import show_error, show_success, show_info
from db import ket_noi
from products import tim_sanpham
from stock import xuat_bo_san_pham_theo_ten
from datetime import datetime

def setup_quantity_spinbox(spinbox, decimals=2, maximum=9999):
    spinbox.setDecimals(decimals)
    spinbox.setMaximum(maximum)
    spinbox.setSingleStep(1)

class XuatBoTab(QWidget):
    def __init__(self, user_id, main_window=None):
        super().__init__()
        self.user_id = user_id
        self.main_window = main_window  # Reference to MainWindow for completer
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # === HÀNG 1: 3 BẢNG CHƯA XUẤT ===
        chua_xuat_layout = QHBoxLayout()

        # Bảng 1: Chưa xuất - Giá Buôn
        buon_layout = QVBoxLayout()
        lbl_buon_chua = QLabel("CHƯA XUẤT - GIÁ BUÔN")
        buon_layout.addWidget(lbl_buon_chua)
        self.tbl_xuatbo_buon = QTableWidget()
        self.tbl_xuatbo_buon.setColumnCount(2)
        self.tbl_xuatbo_buon.setHorizontalHeaderLabels(["Tên sản phẩm", "Số lượng"])
        setup_table(self.tbl_xuatbo_buon)
        buon_layout.addWidget(self.tbl_xuatbo_buon)
        chua_xuat_layout.addLayout(buon_layout)

        # Bảng 2: Chưa xuất - Giá VIP
        vip_layout = QVBoxLayout()
        lbl_vip_chua = QLabel("CHƯA XUẤT - GIÁ VIP")
        vip_layout.addWidget(lbl_vip_chua)
        self.tbl_xuatbo_vip = QTableWidget()
        self.tbl_xuatbo_vip.setColumnCount(2)
        self.tbl_xuatbo_vip.setHorizontalHeaderLabels(["Tên sản phẩm", "Số lượng"])
        setup_table(self.tbl_xuatbo_vip)
        vip_layout.addWidget(self.tbl_xuatbo_vip)
        chua_xuat_layout.addLayout(vip_layout)

        # Bảng 3: Chưa xuất - Giá Lẻ
        le_layout = QVBoxLayout()
        lbl_le_chua = QLabel("CHƯA XUẤT - GIÁ LẺ")
        le_layout.addWidget(lbl_le_chua)
        self.tbl_xuatbo_le = QTableWidget()
        self.tbl_xuatbo_le.setColumnCount(3)
        self.tbl_xuatbo_le.setHorizontalHeaderLabels(
            ["Tên sản phẩm", "Số lượng", "Trạng thái"]
        )
        setup_table(self.tbl_xuatbo_le)
        le_layout.addWidget(self.tbl_xuatbo_le)
        chua_xuat_layout.addLayout(le_layout)

        layout.addLayout(chua_xuat_layout)

        # === HÀNG 2: 3 BẢNG XUẤT DƯ ===
        xuat_du_layout = QHBoxLayout()

        # Bảng 4: Xuất dư - Giá Buôn
        buon_du_layout = QVBoxLayout()
        lbl_buon_du = QLabel("XUẤT DƯ - GIÁ BUÔN")
        buon_du_layout.addWidget(lbl_buon_du)
        self.tbl_xuatdu_buon = QTableWidget()
        self.tbl_xuatdu_buon.setColumnCount(2)
        self.tbl_xuatdu_buon.setHorizontalHeaderLabels(["Tên sản phẩm", "Số lượng"])
        setup_table(self.tbl_xuatdu_buon)
        buon_du_layout.addWidget(self.tbl_xuatdu_buon)
        xuat_du_layout.addLayout(buon_du_layout)

        # Bảng 5: Xuất dư - Giá VIP
        vip_du_layout = QVBoxLayout()
        lbl_vip_du = QLabel("XUẤT DƯ - GIÁ VIP")
        vip_du_layout.addWidget(lbl_vip_du)
        self.tbl_xuatdu_vip = QTableWidget()
        self.tbl_xuatdu_vip.setColumnCount(2)
        self.tbl_xuatdu_vip.setHorizontalHeaderLabels(["Tên sản phẩm", "Số lượng"])
        setup_table(self.tbl_xuatdu_vip)
        vip_du_layout.addWidget(self.tbl_xuatdu_vip)
        xuat_du_layout.addLayout(vip_du_layout)

        # Bảng 6: Xuất dư - Giá Lẻ
        le_du_layout = QVBoxLayout()
        lbl_le_du = QLabel("XUẤT DƯ - GIÁ LẺ")
        le_du_layout.addWidget(lbl_le_du)
        self.tbl_xuatdu_le = QTableWidget()
        self.tbl_xuatdu_le.setColumnCount(2)
        self.tbl_xuatdu_le.setHorizontalHeaderLabels(["Tên sản phẩm", "Số lượng"])
        setup_table(self.tbl_xuatdu_le)
        le_du_layout.addWidget(self.tbl_xuatdu_le)
        xuat_du_layout.addLayout(le_du_layout)

        layout.addLayout(xuat_du_layout)

        # Footer: Form nhập xuất bổ
        lbl_xuat_bo_manual = QLabel("--- XUẤT BỔ THỦ CÔNG ---")
        layout.addWidget(lbl_xuat_bo_manual)
        footer_layout = QVBoxLayout()

        self.xuat_bo_table = QTableWidget()
        self.xuat_bo_table.setColumnCount(4)
        self.xuat_bo_table.setHorizontalHeaderLabels(
            ["Tên sản phẩm", "Số lượng", "Loại giá", "Tiền"]
        )
        setup_table(self.xuat_bo_table)
        self.xuat_bo_table.verticalHeader().setDefaultSectionSize(48)
        self.xuat_bo_table.setColumnWidth(0, 400)
        self.xuat_bo_table.setColumnWidth(1, 120)
        self.xuat_bo_table.setColumnWidth(2, 120)
        self.xuat_bo_table.setMinimumHeight(350)
        footer_layout.addWidget(self.xuat_bo_table)

        bottom_row = QHBoxLayout()
        self.lbl_tong_xuat_bo = QLabel("Tổng: 0")
        bottom_row.addWidget(self.lbl_tong_xuat_bo)
        bottom_row.addStretch()

        btn_refresh = QPushButton("Làm mới")
        btn_refresh.clicked.connect(self.load_xuatbo)
        bottom_row.addWidget(btn_refresh)

        btn_them_dong = QPushButton("Thêm dòng")
        btn_them_dong.clicked.connect(self.them_dong_xuat_bo)
        bottom_row.addWidget(btn_them_dong)

        btn_xuat_bo = QPushButton("XUẤT BỔ")
        btn_xuat_bo.clicked.connect(self.xuat_bo_click)
        bottom_row.addWidget(btn_xuat_bo)

        footer_layout.addLayout(bottom_row)
        layout.addLayout(footer_layout)

        self.load_xuatbo()
        for _ in range(5):
            self.them_dong_xuat_bo()

        self.setLayout(layout)

    def load_xuatbo(self):
        """
        Load dữ liệu cho tab xuất bổ:
        - 3 bảng "Chưa xuất" (VIP, Buôn, Lẻ): Tổng số lượng đã bán (ChiTietHoaDon + DauKyXuatBo) CHƯA trừ xuất dư
        - 3 bảng "Xuất dư" (VIP, Buôn, Lẻ): Số lượng xuất vượt quá số lượng bán

        Logic tính:
        - Chưa xuất = (Tổng bán chưa XHĐ + Nhập đầu kỳ) - (Đã xuất trong XuatDu)
        - Nếu Chưa xuất < 0 => Xuất dư = abs(Chưa xuất), Chưa xuất = 0
        - Nếu Chưa xuất >= 0 => Xuất dư = 0
        """
        conn = ket_noi()
        c = conn.cursor()

        # === 1. TÍNH SỐ LƯỢNG ĐÃ BÁN (chưa xuất hóa đơn) ===
        # Từ ChiTietHoaDon (xuat_hoa_don=0, so_luong > 0)
        c.execute(
            """
            SELECT s.ten, ct.loai_gia, SUM(ct.so_luong)
            FROM ChiTietHoaDon ct
            JOIN SanPham s ON ct.sanpham_id = s.id
            WHERE ct.xuat_hoa_don = 0 AND ct.so_luong > 0
            GROUP BY s.ten, ct.loai_gia
        """
        )
        rows_hoadon = c.fetchall()

        # Từ DauKyXuatBo (nhập đầu kỳ)
        c.execute(
            """
            SELECT ten_sanpham, loai_gia, SUM(so_luong)
            FROM DauKyXuatBo
            GROUP BY ten_sanpham, loai_gia
        """
        )
        rows_dauky = c.fetchall()

        # Tổng hợp: Tổng bán = Bán hàng + Nhập đầu kỳ
        tong_ban = {}
        for ten, loai_gia, sl in rows_hoadon:
            key = (ten, loai_gia)
            tong_ban[key] = tong_ban.get(key, 0) + (sl or 0)
        for ten, loai_gia, sl in rows_dauky:
            key = (ten, loai_gia)
            tong_ban[key] = tong_ban.get(key, 0) + (sl or 0)

        # === 2. TÍNH SỐ LƯỢNG XUẤT DƯ (từ bảng XuatDu) ===
        c.execute(
            """
            SELECT ten_sanpham, loai_gia, SUM(so_luong)
            FROM XuatDu
            GROUP BY ten_sanpham, loai_gia
            """
        )
        rows_xuatdu = c.fetchall()
        xuat_du_tong = {}
        for ten, loai_gia, sl in rows_xuatdu:
            key = (ten, loai_gia)
            xuat_du_tong[key] = xuat_du_tong.get(key, 0) + (sl or 0)

        conn.close()

        # === 3. TÍNH "CHƯA XUẤT" VÀ "XUẤT DƯ" HIỂN THỊ ===
        # Chưa xuất = Tổng bán - Xuất dư
        # Nếu kết quả âm => Xuất dư hiển thị = abs(kết quả), Chưa xuất = 0
        # Nếu kết quả >= 0 => Chưa xuất = kết quả, Xuất dư hiển thị = 0

        chua_xuat_display = {}
        xuat_du_display = {}

        # Lấy tất cả các key từ cả hai nguồn
        all_keys = set(tong_ban.keys()) | set(xuat_du_tong.keys())

        for key in all_keys:
            ban = tong_ban.get(key, 0)
            du = xuat_du_tong.get(key, 0)

            net = ban - du  # Số lượng thực còn chưa xuất

            if net >= 0:
                # Bình thường: còn hàng chưa xuất
                chua_xuat_display[key] = net
                xuat_du_display[key] = 0
            else:
                # Xuất dư: đã xuất nhiều hơn số lượng bán
                chua_xuat_display[key] = 0
                xuat_du_display[key] = abs(net)

        # === 4. PHÂN LOẠI THEO LOẠI GIÁ ===
        data_buon_chua = []
        data_vip_chua = []
        data_le_chua = []
        data_buon_du = []
        data_vip_du = []
        data_le_du = []

        # Chưa xuất
        for (ten, loai_gia), sl in chua_xuat_display.items():
            if sl > 0:
                if loai_gia == "buon":
                    data_buon_chua.append((ten, sl))
                elif loai_gia == "vip":
                    data_vip_chua.append((ten, sl))
                elif loai_gia == "le":
                    data_le_chua.append((ten, sl))

        # Xuất dư
        for (ten, loai_gia), sl in xuat_du_display.items():
            if sl > 0:
                if loai_gia == "buon":
                    data_buon_du.append((ten, sl))
                elif loai_gia == "vip":
                    data_vip_du.append((ten, sl))
                elif loai_gia == "le":
                    data_le_du.append((ten, sl))

        # === 5. LOAD VÀO CÁC BẢNG UI ===
        # Bảng Chưa xuất - Buôn
        self.tbl_xuatbo_buon.setRowCount(len(data_buon_chua))
        for row_idx, (ten, sl) in enumerate(data_buon_chua):
            self.tbl_xuatbo_buon.setItem(row_idx, 0, QTableWidgetItem(ten))
            self.tbl_xuatbo_buon.setItem(row_idx, 1, QTableWidgetItem(str(sl)))

        # Bảng Chưa xuất - VIP
        self.tbl_xuatbo_vip.setRowCount(len(data_vip_chua))
        for row_idx, (ten, sl) in enumerate(data_vip_chua):
            self.tbl_xuatbo_vip.setItem(row_idx, 0, QTableWidgetItem(ten))
            self.tbl_xuatbo_vip.setItem(row_idx, 1, QTableWidgetItem(str(sl)))

        # Bảng Chưa xuất - Lẻ (có cột trạng thái ngưỡng buôn)
        self.tbl_xuatbo_le.setRowCount(len(data_le_chua))

        for row_idx, (ten, sl) in enumerate(data_le_chua):
            self.tbl_xuatbo_le.setItem(row_idx, 0, QTableWidgetItem(ten))
            self.tbl_xuatbo_le.setItem(row_idx, 1, QTableWidgetItem(str(sl)))

            # Tính trạng thái: so sánh với ngưỡng buôn
            sp_info = tim_sanpham(ten)
            if sp_info:
                nguong_buon = sp_info[0][6] if len(sp_info[0]) > 6 else 0
                if sl >= nguong_buon:
                    trang_thai = "Đủ ngưỡng buôn"
                else:
                    trang_thai = "Dưới ngưỡng buôn"
            else:
                trang_thai = "Không xác định"
            self.tbl_xuatbo_le.setItem(row_idx, 2, QTableWidgetItem(trang_thai))

        # Bảng Xuất dư - Buôn
        self.tbl_xuatdu_buon.setRowCount(len(data_buon_du))
        for row_idx, (ten, sl) in enumerate(data_buon_du):
            item_ten = QTableWidgetItem(ten)
            item_sl = QTableWidgetItem(str(sl))
            item_sl.setForeground(Qt.red)  # Màu đỏ cho xuất dư
            self.tbl_xuatdu_buon.setItem(row_idx, 0, item_ten)
            self.tbl_xuatdu_buon.setItem(row_idx, 1, item_sl)

        # Bảng Xuất dư - VIP
        self.tbl_xuatdu_vip.setRowCount(len(data_vip_du))
        for row_idx, (ten, sl) in enumerate(data_vip_du):
            item_ten = QTableWidgetItem(ten)
            item_sl = QTableWidgetItem(str(sl))
            item_sl.setForeground(Qt.red)
            self.tbl_xuatdu_vip.setItem(row_idx, 0, item_ten)
            self.tbl_xuatdu_vip.setItem(row_idx, 1, item_sl)

        # Bảng Xuất dư - Lẻ
        self.tbl_xuatdu_le.setRowCount(len(data_le_du))
        for row_idx, (ten, sl) in enumerate(data_le_du):
            item_ten = QTableWidgetItem(ten)
            item_sl = QTableWidgetItem(str(sl))
            item_sl.setForeground(Qt.red)
            self.tbl_xuatdu_le.setItem(row_idx, 0, item_ten)
            self.tbl_xuatdu_le.setItem(row_idx, 1, item_sl)

    def them_dong_xuat_bo(self):
        row = self.xuat_bo_table.rowCount()
        self.xuat_bo_table.insertRow(row)

        # Cột Tên sản phẩm (với completer)
        ten_edit = QLineEdit()
        # Setup autocomplete nếu có main_window reference
        if self.main_window and hasattr(self.main_window, 'tao_completer_sanpham'):
            ten_edit.setCompleter(self.main_window.tao_completer_sanpham())
        ten_edit.textChanged.connect(lambda: self.update_xuat_bo_row(row))
        self.xuat_bo_table.setCellWidget(row, 0, ten_edit)

        # Cột Số lượng
        sl_spin = QDoubleSpinBox()
        setup_quantity_spinbox(sl_spin, decimals=5, maximum=9999)
        sl_spin.setValue(1.0)
        sl_spin.valueChanged.connect(lambda: self.update_xuat_bo_row(row))
        self.xuat_bo_table.setCellWidget(row, 1, sl_spin)

        # Cột Loại giá
        loai_gia_cb = QComboBox()
        loai_gia_cb.addItems(["le", "buon", "vip"])
        loai_gia_cb.currentTextChanged.connect(lambda: self.update_xuat_bo_row(row))
        self.xuat_bo_table.setCellWidget(row, 2, loai_gia_cb)

        # Cột Tiền
        self.xuat_bo_table.setItem(row, 3, QTableWidgetItem(format_price(0)))

    def update_xuat_bo_row(self, row):
        ten_edit = self.xuat_bo_table.cellWidget(row, 0)
        sl_spin = self.xuat_bo_table.cellWidget(row, 1)
        loai_gia_cb = self.xuat_bo_table.cellWidget(row, 2)

        if not (ten_edit and sl_spin and loai_gia_cb):
            return

        ten = ten_edit.text().strip()
        sl = sl_spin.value()
        loai_gia = loai_gia_cb.currentText()

        if ten:
            res = tim_sanpham(ten)
            if res:
                sp = res[0]
                # Lấy giá theo loại giá
                if loai_gia == "vip":
                    gia = float(sp[4])  # gia_vip
                elif loai_gia == "buon":
                    gia = float(sp[3])  # gia_buon
                else:
                    gia = float(sp[2])  # gia_le

                tien = sl * gia
                self.xuat_bo_table.setItem(row, 3, QTableWidgetItem(format_price(tien)))
            else:
                self.xuat_bo_table.setItem(row, 3, QTableWidgetItem(format_price(0)))
        else:
            self.xuat_bo_table.setItem(row, 3, QTableWidgetItem(format_price(0)))

        # Cập nhật tổng
        self.update_tong_xuat_bo()

    def update_tong_xuat_bo(self):
        tong = 0
        for row in range(self.xuat_bo_table.rowCount()):
            tien_item = self.xuat_bo_table.item(row, 3)
            if tien_item and tien_item.text():
                try:
                    tien = float(tien_item.text().replace(",", ""))
                    tong += tien
                except Exception as e:
                    print(f"Warning: Could not parse money value at row {row}: {e}")
        self.lbl_tong_xuat_bo.setText(f"Tổng: {format_price(tong)}")

    def xuat_bo_click(self):
        # Disable nút để tránh click nhiều lần
        sender = self.sender()
        if sender:
            sender.setEnabled(False)

        try:
            self._xuat_bo_logic()
        finally:
            # Re-enable nút sau khi xong
            if sender:
                sender.setEnabled(True)

    def _xuat_bo_logic(self):
        """
        Logic xuất bổ ĐÚNG:
        - XUẤT LẺ: chỉ lấy từ "Chưa xuất Lẻ" → thiếu → hỏi xuất dư
        - XUẤT BUÔN: kiểm tra ngưỡng → lấy "Chưa xuất Buôn" → thiếu lấy "Chưa xuất Lẻ" → vẫn thiếu → hỏi xuất dư
        - XUẤT VIP: lấy "Chưa xuất VIP" → thiếu lấy "Chưa xuất Buôn" → thiếu lấy "Chưa xuất Lẻ" → vẫn thiếu → hỏi xuất dư

        CHÊNH LỆCH CÔNG ĐOÀN: Tính SAU KHI XUẤT BỔ = (Giá đã bán - Giá xuất bổ) - CHỈ THÔNG BÁO, KHÔNG TRỪ TIỀN
        
        ✅ LỖI 1 FIXED: Trừ TỔNG GIÁ TRỊ XUẤT BỔ vào số dư accountant (không phải chênh lệch công đoàn)
        ✅ LỖI 2 FIXED: Khi mượn sp từ bảng khác, chỉ trừ số lượng cần mượn, giữ lại phần còn lại
        """
        # 1. Lấy danh sách sản phẩm cần xuất
        items = []
        for row in range(self.xuat_bo_table.rowCount()):
            ten_edit = self.xuat_bo_table.cellWidget(row, 0)
            sl_spin = self.xuat_bo_table.cellWidget(row, 1)
            loai_gia_cb = self.xuat_bo_table.cellWidget(row, 2)

            if not (ten_edit and sl_spin and loai_gia_cb):
                continue

            ten = ten_edit.text().strip()
            if not ten:
                continue

            sl_yeu_cau = sl_spin.value()
            loai_gia = loai_gia_cb.currentText()

            items.append({"ten": ten, "so_luong": sl_yeu_cau, "loai_gia": loai_gia})

        if not items:
            show_error(self, "Lỗi", "Không có sản phẩm để xuất")
            return

        # 2. Xử lý từng sản phẩm
        xuat_du_list = []  # [(ten, sl_du, loai_gia)]
        xuat_plan = []  # Chi tiết kế hoạch xuất
        
        tong_gia_tri_xuat_bo = 0  # ✅ FIX LỖI 1: Tính tổng giá trị xuất bổ

        for item in items:
            ten = item["ten"]
            sl_yeu_cau = item["so_luong"]
            loai_gia = item["loai_gia"]

            # Lấy thông tin sản phẩm
            sp_info = tim_sanpham(ten)
            if not sp_info:
                show_error(self, "Lỗi", f"Không tìm thấy sản phẩm '{ten}'")
                return

            sp = sp_info[0]
            gia_le = float(sp[2])
            gia_buon = float(sp[3])
            gia_vip = float(sp[4])
            nguong_buon = sp[6] if len(sp) > 6 else 0

            # Xác định giá xuất bổ
            if loai_gia == "vip":
                gia_xuat_bo = gia_vip
            elif loai_gia == "buon":
                gia_xuat_bo = gia_buon
            else:
                gia_xuat_bo = gia_le
            
            # ✅ FIX LỖI 1: Cộng vào tổng giá trị xuất bổ
            tong_gia_tri_xuat_bo += sl_yeu_cau * gia_xuat_bo

            # Lấy số lượng hiện có
            sl_chua_xuat_le = self.get_sl_from_table("le", ten)
            sl_chua_xuat_buon = self.get_sl_from_table("buon", ten)
            sl_chua_xuat_vip = self.get_sl_from_table("vip", ten)

            # === XỬ LÝ THEO LOẠI GIÁ ===
            plan = {
                "ten": ten,
                "loai_gia_xuat": loai_gia,
                "sl_yeu_cau": sl_yeu_cau,
                "gia_xuat_bo": gia_xuat_bo,
                "chi_tiet": [],  # [(loai_gia_nguon, so_luong)]
            }

            if loai_gia == "le":
                # XUẤT LẺ: chỉ lấy từ bảng chưa xuất lẻ
                if sl_chua_xuat_le >= sl_yeu_cau:
                    # Đủ
                    plan["chi_tiet"].append(("le", sl_yeu_cau))
                else:
                    # Thiếu → hỏi xuất dư
                    thieu = sl_yeu_cau - sl_chua_xuat_le
                    reply = QMessageBox.question(
                        self,
                        "Xuất dư?",
                        f"{ten} - Giá lẻ:\nCó: {sl_chua_xuat_le}\nCần: {sl_yeu_cau}\nThiếu: {thieu}\n\nXuất dư {thieu} sản phẩm?",
                        QMessageBox.Yes | QMessageBox.No,
                    )
                    if reply != QMessageBox.Yes:
                        return

                    # Lấy hết phần có
                    if sl_chua_xuat_le > 0:
                        plan["chi_tiet"].append(("le", sl_chua_xuat_le))

                    # Phần thiếu là xuất dư
                    xuat_du_list.append((ten, thieu, "le"))

            elif loai_gia == "buon":
                # XUẤT BUÔN: kiểm tra ngưỡng, ưu tiên buôn → lẻ
                if sl_yeu_cau < nguong_buon:
                    show_error(
                        self,
                        "Dưới ngưỡng",
                        f"{ten}: Xuất giá buôn phải >= {nguong_buon}\n(Đang yêu cầu: {sl_yeu_cau})",
                    )
                    return

                sl_con_thieu = sl_yeu_cau

                # Lấy từ bảng buôn trước
                if sl_chua_xuat_buon > 0:
                    lay_tu_buon = min(sl_con_thieu, sl_chua_xuat_buon)
                    plan["chi_tiet"].append(("buon", lay_tu_buon))
                    sl_con_thieu -= lay_tu_buon

                # Còn thiếu → lấy từ lẻ
                if sl_con_thieu > 0:
                    reply = QMessageBox.question(
                        self,
                        "Lấy từ giá lẻ?",
                        f"{ten} - Giá buôn thiếu {sl_con_thieu}\nLấy từ bảng chưa xuất giá lẻ?\n(Có: {sl_chua_xuat_le})\n\n→ Sẽ tính chênh lệch công đoàn (CHỈ THÔNG BÁO)",
                        QMessageBox.Yes | QMessageBox.No,
                    )
                    if reply != QMessageBox.Yes:
                        return

                    lay_tu_le = min(sl_con_thieu, sl_chua_xuat_le)
                    if lay_tu_le > 0:
                        plan["chi_tiet"].append(("le", lay_tu_le))
                        sl_con_thieu -= lay_tu_le

                # Vẫn còn thiếu → xuất dư
                if sl_con_thieu > 0:
                    reply = QMessageBox.question(
                        self,
                        "Xuất dư?",
                        f"{ten} - Giá buôn:\nVẫn thiếu: {sl_con_thieu}\n\nXuất dư {sl_con_thieu} sản phẩm?",
                        QMessageBox.Yes | QMessageBox.No,
                    )
                    if reply != QMessageBox.Yes:
                        return

                    xuat_du_list.append((ten, sl_con_thieu, "buon"))

            elif loai_gia == "vip":
                # XUẤT VIP: ưu tiên vip → buôn → lẻ
                sl_con_thieu = sl_yeu_cau

                # Lấy từ VIP trước
                if sl_chua_xuat_vip > 0:
                    lay_tu_vip = min(sl_con_thieu, sl_chua_xuat_vip)
                    plan["chi_tiet"].append(("vip", lay_tu_vip))
                    sl_con_thieu -= lay_tu_vip

                # Thiếu → lấy từ buôn
                if sl_con_thieu > 0 and sl_chua_xuat_buon > 0:
                    reply = QMessageBox.question(
                        self,
                        "Lấy từ giá buôn?",
                        f"{ten} - Giá VIP thiếu {sl_con_thieu}\nLấy từ bảng chưa xuất giá buôn?\n(Có: {sl_chua_xuat_buon})\n\n→ Sẽ tính chênh lệch công đoàn (CHỈ THÔNG BÁO)",
                        QMessageBox.Yes | QMessageBox.No,
                    )
                    if reply != QMessageBox.Yes:
                        return

                    lay_tu_buon = min(sl_con_thieu, sl_chua_xuat_buon)
                    if lay_tu_buon > 0:
                        plan["chi_tiet"].append(("buon", lay_tu_buon))
                        sl_con_thieu -= lay_tu_buon

                # Vẫn thiếu → lấy từ lẻ
                if sl_con_thieu > 0 and sl_chua_xuat_le > 0:
                    reply = QMessageBox.question(
                        self,
                        "Lấy từ giá lẻ?",
                        f"{ten} - Giá VIP vẫn thiếu {sl_con_thieu}\nLấy từ bảng chưa xuất giá lẻ?\n(Có: {sl_chua_xuat_le})\n\n→ Sẽ tính chênh lệch công đoàn (CHỈ THÔNG BÁO)",
                        QMessageBox.Yes | QMessageBox.No,
                    )
                    if reply != QMessageBox.Yes:
                        return

                    lay_tu_le = min(sl_con_thieu, sl_chua_xuat_le)
                    if lay_tu_le > 0:
                        plan["chi_tiet"].append(("le", lay_tu_le))
                        sl_con_thieu -= lay_tu_le

                # Vẫn thiếu → xuất dư
                if sl_con_thieu > 0:
                    reply = QMessageBox.question(
                        self,
                        "Xuất dư?",
                        f"{ten} - Giá VIP:\nVẫn thiếu: {sl_con_thieu}\n\nXuất dư {sl_con_thieu} sản phẩm?",
                        QMessageBox.Yes | QMessageBox.No,
                    )
                    if reply != QMessageBox.Yes:
                        return

                    xuat_du_list.append((ten, sl_con_thieu, "vip"))

            xuat_plan.append(plan)

        # 3. Thực hiện xuất bổ và tính chênh lệch công đoàn (KHÔNG TRỪ TIỀN)
        conn = ket_noi()
        c = conn.cursor()

        tong_chenh_lech_cong_doan = 0  # Chỉ để thông báo
        chenh_lech_chi_tiet = []  # Để hiển thị sau

        try:
            for plan in xuat_plan:
                ten = plan["ten"]
                loai_gia_xuat = plan["loai_gia_xuat"]
                gia_xuat_bo = plan["gia_xuat_bo"]

                for loai_gia_nguon, so_luong in plan["chi_tiet"]:
                    # ✅ FIX LỖI 2: Trừ ĐÚNG số lượng từ từng nguồn
                    # Trừ từ DauKyXuatBo trước (FIFO - nhập sớm nhất xuất trước)
                    c.execute(
                        "SELECT id, so_luong, gia, ngay FROM DauKyXuatBo WHERE ten_sanpham=? AND loai_gia=? ORDER BY ngay ASC, id ASC",
                        (ten, loai_gia_nguon),
                    )
                    dauky_rows = c.fetchall()

                    sl_can_tru = so_luong
                    for row_id, sl_row, gia_ban_dauky, ngay_dauky in dauky_rows:
                        if sl_can_tru <= 0:
                            break
                        tru = min(sl_row, sl_can_tru)

                        # Tính chênh lệch công đoàn: Giá bán - Giá xuất bổ
                        chenh_lech_don_vi = gia_ban_dauky - gia_xuat_bo
                        chenh_lech_phan = chenh_lech_don_vi * tru
                        tong_chenh_lech_cong_doan += chenh_lech_phan

                        if chenh_lech_phan != 0:
                            chenh_lech_chi_tiet.append(
                                {
                                    "ten": ten,
                                    "nguon": f"Đầu kỳ ({loai_gia_nguon})",
                                    "sl": tru,
                                    "gia_ban": gia_ban_dauky,
                                    "gia_xuat": gia_xuat_bo,
                                    "chenh_lech": chenh_lech_phan,
                                }
                            )

                            # Lưu vào bảng ChenhLechXuatBo
                            c.execute("SELECT id FROM SanPham WHERE ten=?", (ten,))
                            sp_row = c.fetchone()
                            if sp_row:
                                sanpham_id = sp_row[0]

                                # Xác định giá mới/cũ dựa trên lịch sử thay đổi giá
                                c.execute(
                                    """
                                    SELECT gia_moi, ngay_thay_doi 
                                    FROM LichSuGia 
                                    WHERE sanpham_id=? AND loai_gia=? 
                                    ORDER BY ngay_thay_doi DESC 
                                    LIMIT 1
                                    """,
                                    (sanpham_id, loai_gia_nguon),
                                )
                                lich_su = c.fetchone()

                                if lich_su:
                                    gia_moi_nhat, ngay_doi = lich_su
                                    is_gia_moi = (
                                        1
                                        if abs(float(gia_ban_dauky) - float(gia_moi_nhat)) < 1e-6
                                        else 0
                                    )
                                else:
                                    # Không có lịch sử thay đổi, coi như giá hiện tại
                                    sp_info = tim_sanpham(ten)
                                    if sp_info:
                                        sp = sp_info[0]
                                        if loai_gia_nguon == "vip":
                                            gia_hien_tai = float(sp[4])
                                        elif loai_gia_nguon == "buon":
                                            gia_hien_tai = float(sp[3])
                                        else:
                                            gia_hien_tai = float(sp[2])
                                        is_gia_moi = (
                                            1
                                            if abs(float(gia_ban_dauky) - float(gia_hien_tai)) < 1e-6
                                            else 0
                                        )
                                    else:
                                        is_gia_moi = 0

                                c.execute(
                                    """
                                    INSERT INTO ChenhLechXuatBo 
                                    (user_id, sanpham_id, ten_sanpham, so_luong, loai_gia_nguon, 
                                     loai_gia_xuat, gia_ban, gia_xuat, chenh_lech, ngay, is_gia_moi)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """,
                                    (
                                        self.user_id,
                                        sanpham_id,
                                        ten,
                                        tru,
                                        loai_gia_nguon,
                                        loai_gia_xuat,
                                        gia_ban_dauky,
                                        gia_xuat_bo,
                                        chenh_lech_phan,
                                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        is_gia_moi,
                                    ),
                                )

                        # ✅ FIX LỖI 2: Trừ đúng số lượng
                        c.execute(
                            "UPDATE DauKyXuatBo SET so_luong=so_luong-? WHERE id=?",
                            (tru, row_id),
                        )
                        c.execute(
                            "DELETE FROM DauKyXuatBo WHERE id=? AND so_luong<=0",
                            (row_id,),
                        )
                        sl_can_tru -= tru

                    # Còn lại thì trừ từ ChiTietHoaDon (FIFO - bán sớm nhất xuất trước)
                    if sl_can_tru > 0:
                        c.execute(
                            """
                            SELECT c.id, c.so_luong, c.gia, h.ngay
                            FROM ChiTietHoaDon c
                            JOIN SanPham s ON c.sanpham_id = s.id
                            JOIN HoaDon h ON c.hoadon_id = h.id
                            WHERE s.ten=? AND c.loai_gia=? AND c.xuat_hoa_don=0 AND c.so_luong > 0
                            ORDER BY h.ngay ASC, c.id ASC
                            """,
                            (ten, loai_gia_nguon),
                        )
                        hd_rows = c.fetchall()

                        for row_id, sl_row, gia_ban_hd, ngay_ban in hd_rows:
                            if sl_can_tru <= 0:
                                break
                            tru = min(sl_row, sl_can_tru)

                            # Tính chênh lệch công đoàn: Giá bán - Giá xuất bổ
                            chenh_lech_don_vi = gia_ban_hd - gia_xuat_bo
                            chenh_lech_phan = chenh_lech_don_vi * tru
                            tong_chenh_lech_cong_doan += chenh_lech_phan

                            if chenh_lech_phan != 0:
                                chenh_lech_chi_tiet.append(
                                    {
                                        "ten": ten,
                                        "nguon": f"Hóa đơn ({loai_gia_nguon})",
                                        "sl": tru,
                                        "gia_ban": gia_ban_hd,
                                        "gia_xuat": gia_xuat_bo,
                                        "chenh_lech": chenh_lech_phan,
                                    }
                                )

                                # Lưu vào bảng ChenhLechXuatBo
                                c.execute("SELECT id FROM SanPham WHERE ten=?", (ten,))
                                sp_row = c.fetchone()
                                if sp_row:
                                    sanpham_id = sp_row[0]

                                    # Xác định giá mới/cũ
                                    c.execute(
                                        """
                                        SELECT gia_moi, ngay_thay_doi 
                                        FROM LichSuGia 
                                        WHERE sanpham_id=? AND loai_gia=? 
                                        ORDER BY ngay_thay_doi DESC 
                                        LIMIT 1
                                        """,
                                        (sanpham_id, loai_gia_nguon),
                                    )
                                    lich_su = c.fetchone()

                                    if lich_su:
                                        gia_moi_nhat, ngay_doi = lich_su
                                        is_gia_moi = (
                                            1
                                            if abs(float(gia_ban_hd) - float(gia_moi_nhat)) < 1e-6
                                            else 0
                                        )
                                    else:
                                        sp_info = tim_sanpham(ten)
                                        if sp_info:
                                            sp = sp_info[0]
                                            if loai_gia_nguon == "vip":
                                                gia_hien_tai = float(sp[4])
                                            elif loai_gia_nguon == "buon":
                                                gia_hien_tai = float(sp[3])
                                            else:
                                                gia_hien_tai = float(sp[2])
                                            is_gia_moi = (
                                                1
                                                if abs(float(gia_ban_hd) - float(gia_hien_tai)) < 1e-6
                                                else 0
                                            )
                                        else:
                                            is_gia_moi = 0

                                    c.execute(
                                        """
                                        INSERT INTO ChenhLechXuatBo 
                                        (user_id, sanpham_id, ten_sanpham, so_luong, loai_gia_nguon, 
                                         loai_gia_xuat, gia_ban, gia_xuat, chenh_lech, ngay, is_gia_moi)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                        """,
                                        (
                                            self.user_id,
                                            sanpham_id,
                                            ten,
                                            tru,
                                            loai_gia_nguon,
                                            loai_gia_xuat,
                                            gia_ban_hd,
                                            gia_xuat_bo,
                                            chenh_lech_phan,
                                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                            is_gia_moi,
                                        ),
                                    )

                            # ✅ FIX LỖI 2: Chỉ đánh dấu xuat_hoa_don=1 cho phần đã xuất, trừ số lượng
                            new_sl = sl_row - tru
                            if new_sl > 0:
                                # Còn lại → Giữ lại record và trừ số lượng
                                c.execute(
                                    "UPDATE ChiTietHoaDon SET so_luong=? WHERE id=?",
                                    (new_sl, row_id),
                                )
                            else:
                                # Hết → Đánh dấu đã xuất
                                c.execute(
                                    "UPDATE ChiTietHoaDon SET xuat_hoa_don=1, so_luong=0 WHERE id=?",
                                    (row_id,),
                                )
                            sl_can_tru -= tru

            # Tạo bản ghi xuất dư (nếu có)
            for ten, sl_du, loai_gia_du in xuat_du_list:
                c.execute("SELECT id FROM SanPham WHERE ten=?", (ten,))
                row = c.fetchone()
                if row:
                    sp_id = row[0]
                    ngay = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    c.execute(
                        """
                        INSERT INTO XuatDu (user_id, sanpham_id, ten_sanpham, so_luong, loai_gia, ngay)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (self.user_id, sp_id, ten, sl_du, loai_gia_du, ngay),
                    )

            # HIỂN THỊ DIALOG XÁC NHẬN
            dialog = QDialog(self)
            dialog.setWindowTitle("Xác nhận xuất bổ")
            dialog.resize(700, 500)
            layout = QVBoxLayout()

            # Hiển thị tổng giá trị xuất bổ (sẽ trừ vào số dư)
            layout.addWidget(
                QLabel(f"<b>💰 TỔNG GIÁ TRỊ XUẤT BỔ: {format_price(tong_gia_tri_xuat_bo)}</b>")
            )
            layout.addWidget(
                QLabel(f"<i>→ Số tiền này sẽ trừ vào số dư của bạn</i>")
            )
            layout.addWidget(QLabel("\n"))

            # Hiển thị chênh lệch công đoàn (CHỈ THÔNG BÁO)
            if chenh_lech_chi_tiet:
                layout.addWidget(QLabel("<b>📊 CHI TIẾT CHÊNH LỆCH CÔNG ĐOÀN (CHỈ THÔNG BÁO):</b>"))

                for item in chenh_lech_chi_tiet:
                    layout.addWidget(
                        QLabel(
                            f"• {item['ten']} ({item['nguon']}): {item['sl']} sp x "
                            f"({format_price(item['gia_ban'])} - {format_price(item['gia_xuat'])}) = "
                            f"{format_price(item['chenh_lech'])}"
                        )
                    )

                layout.addWidget(
                    QLabel(
                        f"\n<b>→ Tổng chênh lệch công đoàn: {format_price(tong_chenh_lech_cong_doan)}</b>"
                    )
                )
                layout.addWidget(
                    QLabel(
                        "<i>⚠️ Chênh lệch công đoàn CHỈ THÔNG BÁO, không trừ vào số dư</i>"
                    )
                )
            else:
                layout.addWidget(QLabel("<b>✅ Không có chênh lệch công đoàn</b>"))

            layout.addWidget(
                QLabel(
                    "\n<i>Bấm OK để xác nhận xuất bổ, hoặc đóng cửa sổ để hủy.</i>"
                )
            )

            btn_layout = QHBoxLayout()
            btn_ok = QPushButton("OK - Xác nhận xuất bổ")
            btn_cancel = QPushButton("Hủy")
            btn_ok.clicked.connect(dialog.accept)
            btn_cancel.clicked.connect(dialog.reject)
            btn_layout.addWidget(btn_cancel)
            btn_layout.addWidget(btn_ok)
            layout.addLayout(btn_layout)

            dialog.setLayout(layout)

            # CHỜ user quyết định
            result = dialog.exec_()

            if result == QDialog.Accepted:
                # User bấm OK → Thực hiện commit
                # ✅ FIX LỖI 1: Trừ TỔNG GIÁ TRỊ XUẤT BỔ (không phải chênh lệch công đoàn)
                if tong_gia_tri_xuat_bo > 0:
                    c.execute(
                        "UPDATE Users SET so_du = so_du - ? WHERE id = ?",
                        (tong_gia_tri_xuat_bo, self.user_id),
                    )
                conn.commit()
                show_success(
                    self,
                    f"✅ Xuất bổ thành công!\n\n"
                    f"💰 Đã trừ {format_price(tong_gia_tri_xuat_bo)} vào số dư\n"
                    f"📊 Chênh lệch công đoàn: {format_price(tong_chenh_lech_cong_doan)} (chỉ thông báo)"
                )
            else:
                # User đóng dialog hoặc bấm Hủy → Rollback
                conn.rollback()
                show_info(self, "Đã hủy", "Đã hủy thao tác xuất bổ")
                conn.close()
                return

            # Làm mới
            self.load_xuatbo()
            self.xuat_bo_table.setRowCount(0)
            for _ in range(5):
                self.them_dong_xuat_bo()

        except Exception as e:
            conn.rollback()
            show_error(self, "Lỗi", f"Lỗi khi xuất bổ: {e}")
            import traceback
            traceback.print_exc()
        finally:
            conn.close()

    def get_sl_from_table(self, loai_gia, ten_sp):
        """Lấy số lượng từ bảng 'Chưa xuất' tương ứng"""
        if loai_gia == "vip":
            table = self.tbl_xuatbo_vip
        elif loai_gia == "buon":
            table = self.tbl_xuatbo_buon
        else:  # le
            table = self.tbl_xuatbo_le

        for row in range(table.rowCount()):
            ten_item = table.item(row, 0)
            if ten_item and ten_item.text() == ten_sp:
                sl_item = table.item(row, 1)
                if sl_item:
                    try:
                        return float(sl_item.text())
                    except:
                        return 0
        return 0

    def get_sl_xuatdu_from_table(self, loai_gia, ten_sp):
        """Lấy số lượng từ bảng 'Xuất dư' tương ứng"""
        if loai_gia == "vip":
            table = self.tbl_xuatdu_vip
        elif loai_gia == "buon":
            table = self.tbl_xuatdu_buon
        else:  # le
            table = self.tbl_xuatdu_le

        for row in range(table.rowCount()):
            ten_item = table.item(row, 0)
            if ten_item and ten_item.text() == ten_sp:
                sl_item = table.item(row, 1)
                if sl_item:
                    try:
                        return float(sl_item.text())
                    except:
                        return 0
        return 0
