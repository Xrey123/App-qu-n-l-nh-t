from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDateEdit, QPushButton, 
    QTableWidget, QTableWidgetItem, QFileDialog, QDialog, QFormLayout, 
    QLineEdit, QDialogButtonBox, QDateTimeEdit
)
from PyQt5.QtCore import Qt, QDate, QDateTime
from gui.utils import setup_table, format_price
from utils.ui_helpers import show_error, show_success, show_warning, show_confirmation
from db import ket_noi
from invoices import (
    export_hoa_don_excel, sua_chi_tiet_hoa_don, xoa_chi_tiet_hoa_don, 
    sua_hoa_don, xoa_hoa_don
)

class InvoiceTab(QWidget):
    def __init__(self, user_id, role):
        super().__init__()
        self.user_id = user_id
        self.role = role
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Filter by date
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Từ ngày:"))
        self.hoadon_tu_ngay = QDateEdit()
        self.hoadon_tu_ngay.setCalendarPopup(True)
        self.hoadon_tu_ngay.setDate(QDate.currentDate().addMonths(-1))
        filter_layout.addWidget(self.hoadon_tu_ngay)

        filter_layout.addWidget(QLabel("Đến ngày:"))
        self.hoadon_den_ngay = QDateEdit()
        self.hoadon_den_ngay.setCalendarPopup(True)
        self.hoadon_den_ngay.setDate(QDate.currentDate())
        filter_layout.addWidget(self.hoadon_den_ngay)

        btn_load = QPushButton("Tải dữ liệu")
        btn_load.clicked.connect(self.load_hoadon)
        filter_layout.addWidget(btn_load)
        filter_layout.addStretch()

        layout.addLayout(filter_layout)

        # Invoice Table
        self.tbl_hoadon = QTableWidget()
        if self.role == "admin":
            self.tbl_hoadon.setColumnCount(8)
            self.tbl_hoadon.setHorizontalHeaderLabels(
                ["ID HĐ", "ID CT", "Ngày", "Username", "Tên SP", "SL", "Loại giá", "Tổng tiền"]
            )
        else:
            self.tbl_hoadon.setColumnCount(6)
            self.tbl_hoadon.setHorizontalHeaderLabels(
                ["Ngày", "Username", "Tên SP", "SL", "Loại giá", "Tổng tiền"]
            )
        setup_table(self.tbl_hoadon)
        layout.addWidget(self.tbl_hoadon)

        # Total Label
        self.lbl_tong_hoadon = QLabel("Tổng XHĐ: 0")
        layout.addWidget(self.lbl_tong_hoadon)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_export = QPushButton("Export Excel")
        btn_export.clicked.connect(self.export_hoadon_excel)
        btn_layout.addWidget(btn_export)

        if self.role == "admin":
            btn_sua_chitiet = QPushButton("✏️ Sửa chi tiết")
            btn_sua_chitiet.clicked.connect(self.sua_chi_tiet_hoadon_admin)
            btn_layout.addWidget(btn_sua_chitiet)

            btn_xoa_chitiet = QPushButton("🗑️ Xóa chi tiết")
            btn_xoa_chitiet.clicked.connect(self.xoa_chi_tiet_hoadon_admin)
            btn_layout.addWidget(btn_xoa_chitiet)

            btn_sua_hoadon = QPushButton("📝 Sửa hóa đơn")
            btn_sua_hoadon.clicked.connect(self.sua_hoadon_admin)
            btn_layout.addWidget(btn_sua_hoadon)

            btn_xoa_hoadon = QPushButton("❌ Xóa hóa đơn")
            btn_xoa_hoadon.clicked.connect(self.xoa_hoadon_admin)
            btn_layout.addWidget(btn_xoa_hoadon)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.load_hoadon()

    def load_hoadon(self):
        tu_ngay = self.hoadon_tu_ngay.date().toString("yyyy-MM-dd")
        den_ngay = self.hoadon_den_ngay.date().toString("yyyy-MM-dd")

        try:
            conn = ket_noi()
            c = conn.cursor()

            if self.role == "admin":
                sql = """
                    SELECT
                        hd.id as hoadon_id,
                        ct.id as chitiet_id,
                        hd.ngay,
                        u.username,
                        s.ten as ten_sp,
                        ct.so_luong,
                        ct.loai_gia,
                        (ct.so_luong * ct.gia - ct.giam) as tong_tien
                    FROM ChiTietHoaDon ct
                    JOIN HoaDon hd ON ct.hoadon_id = hd.id
                    JOIN Users u ON hd.user_id = u.id
                    JOIN SanPham s ON ct.sanpham_id = s.id
                    WHERE ct.xuat_hoa_don = 1
                """
            else:
                sql = """
                    SELECT
                        hd.ngay,
                        u.username,
                        s.ten as ten_sp,
                        ct.so_luong,
                        ct.loai_gia,
                        (ct.so_luong * ct.gia - ct.giam) as tong_tien
                    FROM ChiTietHoaDon ct
                    JOIN HoaDon hd ON ct.hoadon_id = hd.id
                    JOIN Users u ON hd.user_id = u.id
                    JOIN SanPham s ON ct.sanpham_id = s.id
                    WHERE ct.xuat_hoa_don = 1
                """

            params = []
            if self.role == "staff":
                sql += " AND hd.user_id = ?"
                params.append(self.user_id)

            if tu_ngay:
                sql += " AND date(hd.ngay) >= date(?)"
                params.append(tu_ngay)
            if den_ngay:
                sql += " AND date(hd.ngay) <= date(?)"
                params.append(den_ngay)

            sql += " ORDER BY hd.ngay DESC"

            c.execute(sql, params)
            data = c.fetchall()

            self.tbl_hoadon.setRowCount(len(data))
            tong_tien = 0

            for row_idx, row in enumerate(data):
                if self.role == "admin":
                    hoadon_id, chitiet_id, ngay, username, ten_sp, so_luong, loai_gia, tong_tien_item = row
                    loai_gia_text = {"le": "Lẻ", "buon": "Buôn", "vip": "VIP"}.get(loai_gia, loai_gia)

                    self.tbl_hoadon.setItem(row_idx, 0, QTableWidgetItem(str(hoadon_id)))
                    self.tbl_hoadon.setItem(row_idx, 1, QTableWidgetItem(str(chitiet_id)))
                    self.tbl_hoadon.setItem(row_idx, 2, QTableWidgetItem(ngay))
                    self.tbl_hoadon.setItem(row_idx, 3, QTableWidgetItem(username))
                    self.tbl_hoadon.setItem(row_idx, 4, QTableWidgetItem(ten_sp))
                    self.tbl_hoadon.setItem(row_idx, 5, QTableWidgetItem(str(so_luong)))
                    self.tbl_hoadon.setItem(row_idx, 6, QTableWidgetItem(loai_gia_text))
                    self.tbl_hoadon.setItem(row_idx, 7, QTableWidgetItem(format_price(tong_tien_item)))
                else:
                    ngay, username, ten_sp, so_luong, loai_gia, tong_tien_item = row
                    loai_gia_text = {"le": "Lẻ", "buon": "Buôn", "vip": "VIP"}.get(loai_gia, loai_gia)

                    self.tbl_hoadon.setItem(row_idx, 0, QTableWidgetItem(ngay))
                    self.tbl_hoadon.setItem(row_idx, 1, QTableWidgetItem(username))
                    self.tbl_hoadon.setItem(row_idx, 2, QTableWidgetItem(ten_sp))
                    self.tbl_hoadon.setItem(row_idx, 3, QTableWidgetItem(str(so_luong)))
                    self.tbl_hoadon.setItem(row_idx, 4, QTableWidgetItem(loai_gia_text))
                    self.tbl_hoadon.setItem(row_idx, 5, QTableWidgetItem(format_price(tong_tien_item)))

                tong_tien += tong_tien_item

            self.lbl_tong_hoadon.setText(f"Tổng XHĐ: {format_price(tong_tien)}")

        except Exception as e:
            print(f"Lỗi load XHD data: {e}")
        finally:
            conn.close()

    def export_hoadon_excel(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Lưu file Excel", "", "Excel Files (*.xlsx)")
        if file_path:
            if export_hoa_don_excel(file_path, "Da_xuat"):
                show_success(self, "Export thành công")

    def sua_chi_tiet_hoadon_admin(self):
        row = self.tbl_hoadon.currentRow()
        if row < 0:
            show_warning(self, "Vui lòng chọn chi tiết hóa đơn cần sửa")
            return

        chitiet_id = int(self.tbl_hoadon.item(row, 1).text())
        ten_sp = self.tbl_hoadon.item(row, 4).text()
        so_luong_cu = self.tbl_hoadon.item(row, 5).text()

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Sửa chi tiết: {ten_sp}")
        form = QFormLayout()

        txt_so_luong = QLineEdit(so_luong_cu)
        txt_ghi_chu = QLineEdit()

        form.addRow("Số lượng mới:", txt_so_luong)
        form.addRow("Ghi chú:", txt_ghi_chu)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        form.addRow(buttons)
        dialog.setLayout(form)

        if dialog.exec_() == QDialog.Accepted:
            try:
                so_luong_moi = float(txt_so_luong.text())
                ghi_chu = txt_ghi_chu.text().strip() or None

                if sua_chi_tiet_hoa_don(chitiet_id, so_luong=so_luong_moi, ghi_chu=ghi_chu):
                    show_success(self, "Đã sửa chi tiết hóa đơn")
                    self.load_hoadon()
                else:
                    show_error(self, "Lỗi khi sửa chi tiết hóa đơn")
            except ValueError:
                show_error(self, "Số lượng không hợp lệ")

    def xoa_chi_tiet_hoadon_admin(self):
        row = self.tbl_hoadon.currentRow()
        if row < 0:
            show_warning(self, "Vui lòng chọn chi tiết hóa đơn cần xóa")
            return

        chitiet_id = int(self.tbl_hoadon.item(row, 1).text())
        ten_sp = self.tbl_hoadon.item(row, 4).text()

        if not show_confirmation(self, f"Bạn có chắc chắn muốn xóa chi tiết:\n{ten_sp}?\n\n⚠️ Thao tác này không thể hoàn tác!"):
            return

        if xoa_chi_tiet_hoa_don(chitiet_id):
            show_success(self, "Đã xóa chi tiết hóa đơn")
            self.load_hoadon()
        else:
            show_error(self, "Lỗi khi xóa chi tiết hóa đơn")

    def sua_hoadon_admin(self):
        row = self.tbl_hoadon.currentRow()
        if row < 0:
            show_warning(self, "Vui lòng chọn hóa đơn cần sửa")
            return

        hoadon_id = int(self.tbl_hoadon.item(row, 0).text())
        ngay_cu = self.tbl_hoadon.item(row, 2).text()

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Sửa hóa đơn #{hoadon_id}")
        form = QFormLayout()

        txt_ngay = QDateTimeEdit()
        txt_ngay.setDisplayFormat("dd/MM/yyyy HH:mm:ss")
        txt_ngay.setCalendarPopup(True)
        try:
            dt = QDateTime.fromString(ngay_cu, "yyyy-MM-dd HH:mm:ss")
            txt_ngay.setDateTime(dt)
        except:
            txt_ngay.setDateTime(QDateTime.currentDateTime())

        txt_ghi_chu = QLineEdit()

        form.addRow("Ngày giờ:", txt_ngay)
        form.addRow("Ghi chú:", txt_ghi_chu)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        form.addRow(buttons)
        dialog.setLayout(form)

        if dialog.exec_() == QDialog.Accepted:
            ngay_moi = txt_ngay.dateTime().toString("yyyy-MM-dd HH:mm:ss")
            ghi_chu = txt_ghi_chu.text().strip() or None

            if sua_hoa_don(hoadon_id, ngay=ngay_moi, ghi_chu=ghi_chu):
                show_success(self, "Đã sửa hóa đơn")
                self.load_hoadon()
            else:
                show_error(self, "Lỗi khi sửa hóa đơn")

    def xoa_hoadon_admin(self):
        row = self.tbl_hoadon.currentRow()
        if row < 0:
            show_warning(self, "Vui lòng chọn hóa đơn cần xóa")
            return

        hoadon_id = int(self.tbl_hoadon.item(row, 0).text())

        if not show_confirmation(self, f"Bạn có chắc chắn muốn xóa hóa đơn #{hoadon_id}?\n\n⚠️ Tất cả chi tiết hóa đơn liên quan sẽ bị xóa!\n⚠️ Thao tác này không thể hoàn tác!"):
            return

        if xoa_hoa_don(hoadon_id):
            show_success(self, "Đã xóa hóa đơn")
            self.load_hoadon()
        else:
            show_error(self, "Lỗi khi xóa hóa đơn")
