"""
Tab Chi tiết bán - Hiển thị chi tiết các ca bán hàng
Migrated from main_gui.py (dòng 2871-3913, ~1,042 dòng logic)
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QDateEdit, QDialog,
    QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox,
    QHeaderView, QTextEdit
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QDoubleValidator
from datetime import datetime

from db import ket_noi
from invoices import lay_danh_sach_hoadon, lay_chi_tiet_hoadon, xoa_hoa_don
from users import lay_tong_nop_theo_hoadon, lay_tat_ca_user, chuyen_tien
from products import tim_sanpham
from utils.ui_helpers import show_error, show_success, show_warning, show_confirmation, show_info, setup_table
from utils.invoice import tinh_chenh_lech, tinh_unpaid_total
from gui.utils import format_price

# Mệnh giá tiền
MENH_GIA = [500000, 200000, 100000, 50000, 20000, 10000, 5000, 2000, 1000]


class ChiTietBanTab(QWidget):
    def __init__(self, user_id, role, main_window):
        super().__init__()
        self.user_id = user_id
        self.role = role
        self.main_window = main_window
        self.to_tien_spins_nop_tien = []
        self.lbl_tong_to_nop_tien = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Filter theo ngày (thêm theo yêu cầu)
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Từ ngày:"))
        self.chitiet_tu_ngay = QDateEdit()
        self.chitiet_tu_ngay.setCalendarPopup(True)
        self.chitiet_tu_ngay.setDate(QDate.currentDate().addMonths(-1))
        filter_layout.addWidget(self.chitiet_tu_ngay)
        
        filter_layout.addWidget(QLabel("Đến ngày:"))
        self.chitiet_den_ngay = QDateEdit()
        self.chitiet_den_ngay.setCalendarPopup(True)
        self.chitiet_den_ngay.setDate(QDate.currentDate())
        filter_layout.addWidget(self.chitiet_den_ngay)
        
        btn_load = QPushButton("Tải dữ liệu")
        btn_load.clicked.connect(self.load_chitietban)
        filter_layout.addWidget(btn_load)
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        self.tbl_chitietban = QTableWidget()
        self.tbl_chitietban.setColumnCount(8)
        self.tbl_chitietban.setHorizontalHeaderLabels(
            [
                "ID",
                "User ID",
                "Username",
                "Ngày",
                "Trạng thái",
                "Số dư (Nợ)",
                "Chi tiết",
                "Nộp tiền",
            ]
        )
        setup_table(self.tbl_chitietban)
        layout.addWidget(self.tbl_chitietban)
        
        # Nút hành động
        btn_layout = QHBoxLayout()
        btn_refresh = QPushButton("Làm mới")
        btn_refresh.clicked.connect(self.load_chitietban)
        btn_layout.addWidget(btn_refresh)
        
        # Chỉ admin mới có quyền sửa/xóa hóa đơn trong tab này
        if self.role == "admin":
            btn_sua_hd_chitiet = QPushButton("✏️ Sửa ca bán hàng")
            btn_sua_hd_chitiet.clicked.connect(self.sua_hoadon_chitiet_admin)
            btn_layout.addWidget(btn_sua_hd_chitiet)
            
            btn_xoa_hd_chitiet = QPushButton("🗑️ Xóa hóa đơn")
            btn_xoa_hd_chitiet.clicked.connect(self.xoa_hoadon_chitiet_admin)
            btn_layout.addWidget(btn_xoa_hd_chitiet)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        self.load_chitietban()
    
    def load_chitietban(self):
        # Lấy điều kiện lọc ngày nếu có
        tu_ngay = None
        den_ngay = None
        try:
            if hasattr(self, "chitiet_tu_ngay") and hasattr(self, "chitiet_den_ngay"):
                tu_ngay = self.chitiet_tu_ngay.date().toPyDate()
                den_ngay = self.chitiet_den_ngay.date().toPyDate()
        except Exception:
            tu_ngay = None
            den_ngay = None
        
        hoadons = lay_danh_sach_hoadon("Chua_xuat")
        
        # Nếu lọc theo ngày, giữ lại những hóa đơn trong khoảng
        if tu_ngay or den_ngay:
            filtered = []
            for hd in hoadons:
                try:
                    ngay_dt = datetime.strptime(hd[4], "%Y-%m-%d %H:%M:%S").date()
                except Exception:
                    try:
                        ngay_dt = datetime.fromisoformat(hd[4]).date()
                    except Exception:
                        ngay_dt = None
                if ngay_dt is None:
                    filtered.append(hd)
                    continue
                if tu_ngay and ngay_dt < tu_ngay:
                    continue
                if den_ngay and ngay_dt > den_ngay:
                    continue
                filtered.append(hd)
            hoadons = filtered
        
        self.tbl_chitietban.setRowCount(len(hoadons))
        for row_idx, hd in enumerate(hoadons):
            self.tbl_chitietban.setItem(row_idx, 0, QTableWidgetItem(str(hd[0])))  # ID
            self.tbl_chitietban.setItem(row_idx, 1, QTableWidgetItem(str(hd[1])))  # User ID
            self.tbl_chitietban.setItem(row_idx, 2, QTableWidgetItem(hd[2]))  # Username
            self.tbl_chitietban.setItem(row_idx, 3, QTableWidgetItem(hd[4]))  # Ngày
            self.tbl_chitietban.setItem(row_idx, 4, QTableWidgetItem(hd[5]))  # Trạng thái
            
            # Tính số dư = tổng tiền các sản phẩm CHƯA xuất hóa đơn (xuat_hoa_don=0)
            hoadon_id = hd[0]
            chi_tiet = lay_chi_tiet_hoadon(hoadon_id)
            unpaid_total = tinh_unpaid_total(chi_tiet)
            
            # Lấy tổng đã nộp cho hóa đơn này
            try:
                paid = lay_tong_nop_theo_hoadon(hoadon_id)
            except Exception:
                paid = 0
            
            so_du = unpaid_total - (paid or 0)
            if so_du < 0:
                so_du = 0
            
            self.tbl_chitietban.setItem(
                row_idx, 5, QTableWidgetItem(format_price(so_du))
            )  # Số dư
            
            # Thay nút "Chi tiết" bằng text link màu xanh
            link_detail = QLabel(
                f'<a href="#" style="color: #0A6CBF; text-decoration: none; font-weight: bold;">Chi tiết</a>'
            )
            link_detail.setAlignment(Qt.AlignCenter)
            link_detail.setOpenExternalLinks(False)
            link_detail.linkActivated.connect(lambda _, r=row_idx: self.xem_chi_tiet(r))
            link_detail.setCursor(Qt.PointingHandCursor)
            self.tbl_chitietban.setCellWidget(row_idx, 6, link_detail)
            
            # Nút "Nộp tiền cho Accountant"
            if so_du > 0:
                btn_nop = QPushButton("💰 Nộp cho Accountant")
                btn_nop.setStyleSheet(
                    "background-color: #4CAF50; color: white; font-weight: bold;"
                )
                btn_nop.clicked.connect(lambda checked, r=row_idx: self.nop_tien(r))
                self.tbl_chitietban.setCellWidget(row_idx, 7, btn_nop)
            else:
                lbl_done = QLabel("✅ Đã thanh toán")
                lbl_done.setAlignment(Qt.AlignCenter)
                lbl_done.setStyleSheet("color: green; font-weight: bold;")
                self.tbl_chitietban.setCellWidget(row_idx, 7, lbl_done)
        
        # Ẩn cột không cần hiển thị
        self.tbl_chitietban.setColumnHidden(0, True)  # ID
        self.tbl_chitietban.setColumnHidden(1, True)  # User ID
        self.tbl_chitietban.setColumnHidden(4, True)  # Trạng thái
    
    def xem_chi_tiet(self, row):
        """Hiển thị dialog chi tiết hóa đơn với 2 bảng: đã XHĐ và chưa XHĐ"""
        hoadon_id = int(self.tbl_chitietban.item(row, 0).text())
        username = self.tbl_chitietban.item(row, 2).text()
        ngay = self.tbl_chitietban.item(row, 3).text()
        data = lay_chi_tiet_hoadon(hoadon_id)
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Chi tiết hóa đơn")
        dialog.resize(800, 600)
        layout = QVBoxLayout()
        
        # Thông tin hóa đơn
        layout.addWidget(QLabel(f"Ngày: {ngay} - Username: {username}"))
        
        # Bảng đã xuất hóa đơn
        lbl_da = QLabel("Đã xuất hóa đơn")
        layout.addWidget(lbl_da)
        tbl_da = QTableWidget()
        tbl_da.setColumnCount(7)
        tbl_da.setHorizontalHeaderLabels(
            ["Tên SP", "SL", "Loại giá", "Giá", "Tổng", "Chênh lệch", "Ghi chú"]
        )
        da_xuat = [row for row in data if row[7] == 1]
        tbl_da.setRowCount(len(da_xuat))
       
        for r_idx, row_data in enumerate(da_xuat):
            self._fill_detail_table_row(tbl_da, r_idx, row_data)
        layout.addWidget(tbl_da)
        
        # Bảng chưa xuất hóa đơn
        lbl_chua = QLabel("Chưa xuất hóa đơn")
        layout.addWidget(lbl_chua)
        tbl_chua = QTableWidget()
        tbl_chua.setColumnCount(7)
        tbl_chua.setHorizontalHeaderLabels(
            ["Tên SP", "SL", "Loại giá", "Giá", "Tổng", "Chênh lệch", "Ghi chú"]
        )
        chua_xuat = [row for row in data if row[7] == 0]
        tbl_chua.setRowCount(len(chua_xuat))
        
        for r_idx, row_data in enumerate(chua_xuat):
            self._fill_detail_table_row(tbl_chua, r_idx, row_data)
        layout.addWidget(tbl_chua)
        
        # Nút đóng
        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(dialog.close)
        layout.addWidget(btn_close)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def _fill_detail_table_row(self, table, r_idx, row_data):
        """Helper để fill 1 dòng trong bảng chi tiết"""
        table.setItem(r_idx, 0, QTableWidgetItem(row_data[3]))  # ten
        table.setItem(r_idx, 1, QTableWidgetItem(str(row_data[4])))  # so_luong
        loai_gia_text = {"le": "Lẻ", "buon": "Buôn", "vip": "VIP"}.get(
            row_data[5], row_data[5]
        )
        table.setItem(r_idx, 2, QTableWidgetItem(loai_gia_text))  # loai_gia
        table.setItem(r_idx, 3, QTableWidgetItem(format_price(row_data[6])))  # gia
        tong = row_data[4] * row_data[6] - row_data[9]  # so_luong * gia - giam
        table.setItem(r_idx, 4, QTableWidgetItem(format_price(tong)))
        
        # Tính chênh lệch
        lg = row_data[5]
        xhd = row_data[7]
        sl = row_data[4]
        gia_le = row_data[8]
        giam = row_data[9]
        
        gia_buon_val = None
        if str(lg).lower() == "le":
            sp_info = tim_sanpham(row_data[3])
            if sp_info:
                gia_buon_val = sp_info[0][3]
        
        chenh = tinh_chenh_lech(lg, xhd, sl, gia_le, giam, gia_buon_val)
        table.setItem(r_idx, 5, QTableWidgetItem(format_price(chenh)))
        ghi_chu = row_data[10] if len(row_data) > 10 else ""
        table.setItem(r_idx, 6, QTableWidgetItem(ghi_chu))
    
    def nop_tien(self, row):
        """Dialog nộp tiền cho Accountant"""
        try:
            hoadon_id = int(self.tbl_chitietban.item(row, 0).text())
        except Exception:
            show_error(self, "Lỗi", "Không lấy được ID hóa đơn")
            return
        
        try:
            user_id_from = int(self.tbl_chitietban.item(row, 1).text())
        except Exception:
            user_id_from = None
        
        username_from = (
            self.tbl_chitietban.item(row, 2).text()
            if self.tbl_chitietban.item(row, 2)
            else ""
        )
        
        # Tính số dư hiện tại
        chi_tiet = lay_chi_tiet_hoadon(hoadon_id)
        unpaid_total = tinh_unpaid_total(chi_tiet)
        try:
            paid = lay_tong_nop_theo_hoadon(hoadon_id)
        except Exception:
            paid = 0
        so_du_hien_tai = unpaid_total - (paid or 0)
        if so_du_hien_tai < 0:
            so_du_hien_tai = 0
        
        # Tìm user accountant
        users = lay_tat_ca_user()
        accountant_id = None
        accountant_username = None
        for user in users:
            if user[2] == "accountant":
                accountant_id = user[0]
                accountant_username = user[1]
                break
        
        if not accountant_id:
            show_error(self, "Lỗi", "Không tìm thấy user accountant")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("💰 Nộp tiền cho Accountant")
        layout = QVBoxLayout()
        
        # Thông tin nộp tiền
        layout.addWidget(QLabel(f"<h2>PHIẾU NỘP TIỀN CHO ACCOUNTANT</h2>"))
        layout.addWidget(
            QLabel(f"<b>Ngày:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        )
        layout.addWidget(QLabel(f"<b>Từ:</b> {username_from} (Nhân viên bán hàng)"))
        layout.addWidget(
            QLabel(f"<b>Đến:</b> {accountant_username} (Accountant - Quản lý xuất bổ)")
        )
        layout.addWidget(
            QLabel(
                f"<b>Số tiền còn nợ:</b> <span style='color: red; font-size: 14pt;'>{format_price(so_du_hien_tai)}</span>"
            )
        )
        layout.addWidget(QLabel(""))
        layout.addWidget(
            QLabel("<i>💡 Nộp tiền để Accountant có tiền xuất bổ cho khách</i>")
        )
        layout.addWidget(QLabel(""))
        
        # Nhập số tiền nộp
        tien_layout = QHBoxLayout()
        tien_layout.addWidget(QLabel("<b>Số tiền nộp:</b>"))
        so_tien_edit = QLineEdit()
        so_tien_edit.setPlaceholderText(f"Tối đa {format_price(so_du_hien_tai)}")
        so_tien_edit.setText(str(int(so_du_hien_tai)))  # Mặc định nộp hết
        so_tien_edit.setStyleSheet("font-size: 14pt; padding: 5px;")
        tien_layout.addWidget(so_tien_edit)
        layout.addLayout(tien_layout)
        
        # Đếm tờ tiền
        to_tien_layout = QVBoxLayout()
        to_tien_layout.addWidget(QLabel("Đếm tờ:"))
        self.to_tien_spins_nop_tien = []
        for mg in MENH_GIA:
            hl = QHBoxLayout()
            hl.addWidget(QLabel(format_price(mg)))
            spin = QSpinBox()
            spin.setMaximum(9999)
            spin.valueChanged.connect(
                lambda v, m=mg: self.update_tong_to_tien_nop_tien()
            )
            hl.addWidget(spin)
            to_tien_layout.addLayout(hl)
            self.to_tien_spins_nop_tien.append((spin, mg))
        layout.addLayout(to_tien_layout)
        self.lbl_tong_to_nop_tien = QLabel("Tổng từ tờ: 0")
        layout.addWidget(self.lbl_tong_to_nop_tien)
        
        # Nút xác nhận
        btn_confirm = QPushButton("✅ Xác nhận nộp tiền cho Accountant")
        btn_confirm.setStyleSheet(
            "background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; font-size: 12pt;"
        )
        btn_confirm.clicked.connect(
            lambda: self.xac_nhan_nop_tien(
                user_id_from,
                accountant_id,
                so_tien_edit.text(),
                so_du_hien_tai,
                dialog,
                row,
                hoadon_id,
            )
        )
        layout.addWidget(btn_confirm)
        
        # Nút đóng
        btn_close = QPushButton("❌ Hủy")
        btn_close.setStyleSheet("padding: 8px;")
        btn_close.clicked.connect(dialog.close)
        layout.addWidget(btn_close)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def update_tong_to_tien_nop_tien(self):
        """Update tổng từ tờ tiền"""
        tong = 0
        for spin, mg in self.to_tien_spins_nop_tien:
            tong += spin.value() * mg
        if self.lbl_tong_to_nop_tien:
            self.lbl_tong_to_nop_tien.setText(f"Tổng từ tờ: {format_price(tong)}")
    
    def xac_nhan_nop_tien(
        self, user_id_from, accountant_id, so_tien_str, so_du_max, dialog, row, hoadon_id
    ):
        """Xác nhận nộp tiền"""
        try:
            so_tien = float(so_tien_str.replace(",", ""))
        except Exception:
            show_error(self, "Lỗi", "Số tiền không hợp lệ")
            return
        
        if so_tien <= 0:
            show_error(self, "Lỗi", "Số tiền phải lớn hơn 0")
            return
        
        if so_tien > so_du_max:
            show_error(self, "Lỗi", f"Số tiền nộp không được vượt quá {format_price(so_du_max)}")
            return
        
        # Chuyển tiền từ user_from sang accountant
        try:
            chuyen_tien(user_id_from, accountant_id, so_tien, 
                       ghi_chu=f"Nộp tiền ca bán hàng - HĐ #{hoadon_id}", 
                       hoadon_id=hoadon_id)
            
            # Ghi log vào GiaoDichQuy (đã ghi trong chuyen_tien)
            show_success(self, f"Đã nộp {format_price(so_tien)} cho Accountant")
            dialog.close()
            
            # ✅ REFRESH ALL TABS to update data everywhere
            if hasattr(self.main_window, 'refresh_all_tabs'):
                self.main_window.refresh_all_tabs()
            else:
                # Fallback: just reload this tab
                self.load_chitietban()
        except Exception as e:
            show_error(self, "Lỗi", f"Lỗi nộp tiền: {e}")
    
    def sua_hoadon_chitiet_admin(self):
        """Admin sửa toàn bộ ca bán hàng (chi tiết sản phẩm)"""
        from invoices import lay_chi_tiet_hoadon
        from PyQt5.QtWidgets import QCheckBox
        
        row = self.tbl_chitietban.currentRow()
        if row < 0:
            show_warning(self, "Vui lòng chọn ca bán hàng cần sửa")
            return
        
        hoadon_id = int(self.tbl_chitietban.item(row, 0).text())
        username = self.tbl_chitietban.item(row, 2).text()
        ngay = self.tbl_chitietban.item(row, 3).text()
        
        # Lấy chi tiết hóa đơn hiện tại
        chi_tiet = lay_chi_tiet_hoadon(hoadon_id)
        
        # Tạo dialog để sửa
        dialog = QDialog(self)
        dialog.setWindowTitle(f"✏️ Sửa ca bán hàng #{hoadon_id} - {username} - {ngay}")
        dialog.resize(1200, 600)
        layout = QVBoxLayout()
        
        # Thông tin header
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel(f"<b>Hóa đơn #{hoadon_id}</b>"))
        info_layout.addWidget(QLabel(f"User: {username}"))
        info_layout.addWidget(QLabel(f"Ngày: {ngay}"))
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        # Bảng chi tiết sản phẩm (cho phép sửa)
        tbl_edit = QTableWidget()
        tbl_edit.setColumnCount(9)
        tbl_edit.setHorizontalHeaderLabels(
            [
                "ID",
                "Tên sản phẩm",
                "SL",
                "Đơn giá",
                "Giảm giá",
                "VIP",
                "XHD",
                "Ghi chú",
                "Người cho nợ",
            ]
        )
        
        # Ẩn cột ID
        tbl_edit.setColumnHidden(0, True)
        
        # Load dữ liệu hiện tại
        tbl_edit.setRowCount(len(chi_tiet))
        
        # Lấy danh sách user cho dropdown "Người cho nợ"
        users = lay_tat_ca_user()
        user_dict = {u[0]: u[1] for u in users}  # {user_id: username}
        
        for idx, ct in enumerate(chi_tiet):
            # Query: c.id, c.hoadon_id, c.sanpham_id, s.ten, c.so_luong, c.loai_gia, c.gia, c.xuat_hoa_don, s.gia_le, c.giam, c.ghi_chu
            chitiet_id = ct[0]  # c.id
            sanpham_id = ct[2]  # c.sanpham_id
            ten_sp = ct[3]  # s.ten
            so_luong = ct[4]  # c.so_luong
            loai_gia = ct[5]  # c.loai_gia
            gia = ct[6]  # c.gia
            xuat_hoa_don = ct[7] if len(ct) > 7 else 0  # c.xuat_hoa_don
            giam = ct[9] if len(ct) > 9 else 0  # c.giam
            ghi_chu = ct[10] if len(ct) > 10 else ""  # c.ghi_chu
            
            # Cột 0: ID chi tiết (ẩn)
            tbl_edit.setItem(idx, 0, QTableWidgetItem(str(chitiet_id)))
            
            # Cột 1: Tên sản phẩm (có autocomplete)
            item_ten = QTableWidgetItem(ten_sp)
            tbl_edit.setItem(idx, 1, item_ten)
            
            # Cột 2: Số lượng (QDoubleSpinBox)
            sl_spin = QDoubleSpinBox()
            sl_spin.setMinimum(0.001)
            sl_spin.setMaximum(99999)
            sl_spin.setDecimals(3)
            sl_spin.setValue(float(so_luong))
            tbl_edit.setCellWidget(idx, 2, sl_spin)
            
            # Cột 3: Đơn giá (editable)
            item_gia = QTableWidgetItem(str(int(gia)))
            tbl_edit.setItem(idx, 3, item_gia)
            
            # Cột 4: Giảm giá (QDoubleSpinBox)
            giam_spin = QDoubleSpinBox()
            giam_spin.setMinimum(0)
            giam_spin.setMaximum(999999)
            giam_spin.setDecimals(2)
            giam_spin.setValue(float(giam))
            tbl_edit.setCellWidget(idx, 4, giam_spin)
            
            # Cột 5: VIP (checkbox)
            vip_check = QCheckBox()
            is_vip = loai_gia and "vip" in loai_gia.lower()
            vip_check.setChecked(is_vip)
            tbl_edit.setCellWidget(idx, 5, vip_check)
            
            # Cột 6: XHD (checkbox)
            xhd_check = QCheckBox()
            xhd_check.setChecked(bool(xuat_hoa_don))
            tbl_edit.setCellWidget(idx, 6, xhd_check)
            
            # Cột 7: Ghi chú (editable)
            item_ghi_chu = QTableWidgetItem(ghi_chu or "")
            tbl_edit.setItem(idx, 7, item_ghi_chu)
            
            # Cột 8: Người cho nợ (QComboBox)
            cho_no_combo = QComboBox()
            cho_no_combo.addItem("-- Không --", None)
            
            # Thêm danh sách user
            for user in users:
                cho_no_combo.addItem(f"{user[1]}", user[0])
            
            # TODO: Lấy thông tin người cho nợ từ ghi chú hoặc bảng riêng
            # Hiện tại để mặc định "-- Không --"
            
            tbl_edit.setCellWidget(idx, 8, cho_no_combo)
        
        setup_table(tbl_edit)
        layout.addWidget(tbl_edit)
        
        # Nút thêm/xóa dòng
        btn_row_layout = QHBoxLayout()
        btn_row_layout.addStretch()
        
        btn_them_dong = QPushButton("➕ Thêm dòng")
        btn_them_dong.clicked.connect(
            lambda: self.them_dong_sua_chitiet(tbl_edit, users)
        )
        btn_row_layout.addWidget(btn_them_dong)
        
        btn_xoa_dong = QPushButton("➖ Xóa dòng")
        btn_xoa_dong.clicked.connect(lambda: self.xoa_dong_sua_chitiet(tbl_edit))
        btn_row_layout.addWidget(btn_xoa_dong)
        
        layout.addLayout(btn_row_layout)
        
        # Nút lưu và đóng
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_luu = QPushButton("💾 Lưu thay đổi")
        btn_luu.setStyleSheet(
            "background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;"
        )
        btn_luu.clicked.connect(
            lambda: self.luu_sua_chitiet(dialog, hoadon_id, tbl_edit)
        )
        btn_layout.addWidget(btn_luu)
        
        btn_close = QPushButton("❌ Đóng")
        btn_close.clicked.connect(dialog.close)
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def them_dong_sua_chitiet(self, table, users):
        """Thêm dòng mới vào bảng sửa chi tiết"""
        from PyQt5.QtWidgets import QCheckBox
        
        row = table.rowCount()
        table.insertRow(row)
        
        # Cột 0: ID (để trống cho dòng mới)
        table.setItem(row, 0, QTableWidgetItem("0"))
        
        # Cột 1: Tên sản phẩm
        table.setItem(row, 1, QTableWidgetItem(""))
        
        # Cột 2: Số lượng
        sl_spin = QDoubleSpinBox()
        sl_spin.setMinimum(0.001)
        sl_spin.setMaximum(99999)
        sl_spin.setDecimals(3)
        sl_spin.setValue(1.0)
        table.setCellWidget(row, 2, sl_spin)
        
        # Cột 3: Đơn giá
        table.setItem(row, 3, QTableWidgetItem("0"))
        
        # Cột 4: Giảm giá
        giam_spin = QDoubleSpinBox()
        giam_spin.setMinimum(0)
        giam_spin.setMaximum(999999)
        giam_spin.setDecimals(2)
        giam_spin.setValue(0)
        table.setCellWidget(row, 4, giam_spin)
        
        # Cột 5: VIP
        vip_check = QCheckBox()
        table.setCellWidget(row, 5, vip_check)
        
        # Cột 6: XHD
        xhd_check = QCheckBox()
        table.setCellWidget(row, 6, xhd_check)
        
        # Cột 7: Ghi chú
        table.setItem(row, 7, QTableWidgetItem(""))
        
        # Cột 8: Người cho nợ
        cho_no_combo = QComboBox()
        cho_no_combo.addItem("-- Không --", None)
        for user in users:
            cho_no_combo.addItem(f"{user[1]}", user[0])
        table.setCellWidget(row, 8, cho_no_combo)
    
    def xoa_dong_sua_chitiet(self, table):
        """Xóa dòng được chọn"""
        from PyQt5.QtWidgets import QMessageBox
        
        row = table.currentRow()
        if row >= 0:
            reply = QMessageBox.question(
                self,
                "Xác nhận xóa",
                f"Xóa dòng {row + 1}?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                table.removeRow(row)
    
    def luu_sua_chitiet(self, dialog, hoadon_id, table):
        """Lưu thay đổi chi tiết hóa đơn"""
        try:
            # Thu thập dữ liệu từ bảng
            chi_tiet_moi = []
            
            for row in range(table.rowCount()):
                # Lấy dữ liệu từ các widget
                chitiet_id_item = table.item(row, 0)
                chitiet_id = int(chitiet_id_item.text()) if chitiet_id_item else 0
                
                ten_sp_item = table.item(row, 1)
                if not ten_sp_item or not ten_sp_item.text().strip():
                    continue  # Bỏ qua dòng rỗng
                
                ten_sp = ten_sp_item.text().strip()
                
                # Tìm sản phẩm
                sp_result = tim_sanpham(ten_sp)
                if not sp_result:
                    show_error(
                        self, "Lỗi", f"Dòng {row+1}: Sản phẩm '{ten_sp}' không tồn tại"
                    )
                    return
                
                sanpham_id = sp_result[0][0]
                
                # Lấy các giá trị khác
                sl_spin = table.cellWidget(row, 2)
                so_luong = sl_spin.value() if sl_spin else 1.0
                
                gia_item = table.item(row, 3)
                gia = float(gia_item.text()) if gia_item else 0
                
                giam_spin = table.cellWidget(row, 4)
                giam = giam_spin.value() if giam_spin else 0
                
                vip_check = table.cellWidget(row, 5)
                is_vip = vip_check.isChecked() if vip_check else False
                loai_gia = "vip" if is_vip else "le"
                
                xhd_check = table.cellWidget(row, 6)
                xuat_hoa_don = 1 if (xhd_check and xhd_check.isChecked()) else 0
                
                ghi_chu_item = table.item(row, 7)
                ghi_chu = ghi_chu_item.text().strip() if ghi_chu_item else ""
                
                cho_no_combo = table.cellWidget(row, 8)
                cho_no_user_id = cho_no_combo.currentData() if cho_no_combo else None
                
                chi_tiet_moi.append(
                    {
                        "chitiet_id": chitiet_id,
                        "sanpham_id": sanpham_id,
                        "so_luong": so_luong,
                        "gia": gia,
                        "loai_gia": loai_gia,
                        "giam": giam,
                        "xuat_hoa_don": xuat_hoa_don,
                        "ghi_chu": ghi_chu,
                        "cho_no_user_id": cho_no_user_id,
                    }
                )
            
            if not chi_tiet_moi:
                show_error(self, "Lỗi", "Không có sản phẩm nào để lưu")
                return
            
            # Bắt đầu transaction
            conn = ket_noi()
            c = conn.cursor()
            
            # Lấy thông tin hóa đơn để biết user_id (người bán ban đầu)
            c.execute("SELECT user_id, ngay FROM HoaDon WHERE id = ?", (hoadon_id,))
            hd_info = c.fetchone()
            if not hd_info:
                show_error(self, "Lỗi", "Không tìm thấy hóa đơn")
                conn.close()
                return
            
            user_ban_id = hd_info[0]
            ngay_hd = hd_info[1]
            
            # Xóa tất cả chi tiết cũ
            c.execute("DELETE FROM ChiTietHoaDon WHERE hoadon_id = ?", (hoadon_id,))
            
            # Thêm chi tiết mới và xử lý chuyển tiền cho người cho nợ
            for ct in chi_tiet_moi:
                c.execute(
                    """
                    INSERT INTO ChiTietHoaDon 
                    (hoadon_id, sanpham_id, so_luong, gia, loai_gia, giam, xuat_hoa_don, ghi_chu)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        hoadon_id,
                        ct["sanpham_id"],
                        ct["so_luong"],
                        ct["gia"],
                        ct["loai_gia"],
                        ct["giam"],
                        ct["xuat_hoa_don"],
                        ct["ghi_chu"],
                    ),
                )
                
                # Nếu có người cho nợ, tạo giao dịch chuyển tiền
                if ct["cho_no_user_id"]:
                    tien_chuyen = ct["so_luong"] * ct["gia"] - ct["giam"]
                    
                    # Lấy username của người cho nợ
                    c.execute(
                        "SELECT username FROM Users WHERE id = ?",
                        (ct["cho_no_user_id"],),
                    )
                    user_cho_no = c.fetchone()
                    if user_cho_no:
                        username_cho_no = user_cho_no[0]
                        
                        # Lấy tên sản phẩm từ database
                        c.execute(
                            "SELECT ten FROM SanPham WHERE id = ?", (ct["sanpham_id"],)
                        )
                        sp_row = c.fetchone()
                        ten_sp = sp_row[0] if sp_row else "Sản phẩm"
                        
                        ghi_chu_gd = f"[ADMIN SỬA] Cho nợ {username_cho_no}: {ten_sp} x{ct['so_luong']}"
                        if ct["ghi_chu"]:
                            ghi_chu_gd += f" - {ct['ghi_chu']}"
                        
                        # Ghi giao dịch
                        c.execute(
                            "INSERT INTO GiaoDichQuy (user_id, user_nhan_id, so_tien, ngay, ghi_chu) VALUES (?, ?, ?, ?, ?)",
                            (
                                user_ban_id,
                                ct["cho_no_user_id"],
                                tien_chuyen,
                                ngay_hd,
                                ghi_chu_gd,
                            ),
                        )
            
            conn.commit()
            conn.close()
            
            show_success(self, "Đã lưu thay đổi thành công!")
            dialog.close()
            self.load_chitietban()  # Reload
            
        except Exception as e:
            show_error(self, "Lỗi", f"Lỗi lưu: {e}")
            if 'conn' in locals():
                conn.rollback()
                conn.close()
    
    def xoa_hoadon_chitiet_admin(self):
        """Chỉ admin mới được xóa hóa đơn trong tab Chi tiết bán"""
        row = self.tbl_chitietban.currentRow()
        if row < 0:
            show_warning(self, "Vui lòng chọn hóa đơn cần xóa")
            return
        
        hoadon_id = int(self.tbl_chitietban.item(row, 0).text())
        
        if not show_confirmation(
            self,
            f"Bạn có chắc chắn muốn xóa hóa đơn #{hoadon_id}?\n\n"
            "⚠️ Tất cả chi tiết hóa đơn liên quan sẽ bị xóa!\n"
            "⚠️ Thao tác này không thể hoàn tác!",
        ):
            return
        
        if xoa_hoa_don(hoadon_id):
            show_success(self, "Đã xóa hóa đơn")
            self.load_chitietban()
        else:
            show_error(self, "Lỗi khi xóa hóa đơn")
