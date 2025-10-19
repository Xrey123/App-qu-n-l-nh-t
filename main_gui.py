import sys
import pandas as pd
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QComboBox,
    QTabWidget,
    QHBoxLayout,
    QFileDialog,
    QInputDialog,
    QSpinBox,
    QCompleter,
    QCheckBox,
    QDateEdit,
    QDialog,
    QTextEdit,
    QDialogButtonBox,
    QDoubleSpinBox,
    QStyledItemDelegate,
    QHeaderView,
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtGui import QPainter, QDoubleValidator

# Import các hàm từ module riêng
from users import (
    dang_nhap,
    them_user,
    lay_tat_ca_user,
    xoa_user,
    doi_mat_khau,
    chuyen_tien,
    lay_so_du,
    lay_lich_su_quy,
)
from products import (
    them_sanpham,
    tim_sanpham,
    lay_tat_ca_sanpham,
    import_sanpham_from_dataframe,
    xoa_sanpham,
    lay_danh_sach_ten_sanpham,
    cap_nhat_ton,
)
from invoices import (
    tao_hoa_don,
    lay_danh_sach_hoadon,
    lay_chi_tiet_hoadon,
    xuat_hoa_don,
    export_hoa_don_excel,
    lay_chi_tiet_hoadon_da_xuat,
)
from reports import (
    chi_tiet_log_kho,
    doanh_thu_theo_thang,
    bao_cao_xuat_theo_thang,
    bao_cao_kho,
    bao_cao_doanh_thu,
)
from stock import (
    lay_san_pham_chua_xuat,
    xuat_bo_san_pham,
    lay_tong_chua_xuat_theo_sp,
    lay_bao_cao_cong_doan,
    lay_san_pham_chua_xuat_theo_loai_gia,
    xuat_bo_san_pham_theo_ten,
)
from db import ket_noi, khoi_tao_db

# Định dạng giá
import locale

locale.setlocale(locale.LC_ALL, "en_US.UTF-8")


def format_price(value):
    try:
        return locale.format_string("%.2f", value, grouping=True)
    except:
        return str(value)


class CompleterDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.completer = None

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        if self.completer:
            editor.setCompleter(self.completer)
            editor.textChanged.connect(self.on_text_changed)
        return editor

    def on_text_changed(self, text):
        if self.completer:
            self.completer.setCompletionPrefix(text)
            self.completer.complete()


class DangNhap(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dang nhap")
        self.resize
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Username"))
        self.user_edit = QLineEdit()
        layout.addWidget(self.user_edit)
        layout.addWidget(QLabel("Password"))
        self.pwd_edit = QLineEdit()
        self.pwd_edit.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.pwd_edit)
        btn = QPushButton("Dang nhap")
        btn.clicked.connect(self.dang_nhap_click)
        layout.addWidget(btn)
        self.setLayout(layout)

    def dang_nhap_click(self):
        username = self.user_edit.text().strip()
        pwd = self.pwd_edit.text().strip()
        user = dang_nhap(username, pwd)
        if not user:
            QMessageBox.warning(self, "Lỗi", "Sai tài khoản hoặc mật khẩu")
            return
        self.user_id, self.role = user
        self.main_win = MainWindow(self.user_id, self.role, self)
        self.main_win.show()
        self.hide()


class MainWindow(QWidget):
    def __init__(self, user_id, role, login_window):
        super().__init__()
        self.user_id = user_id
        self.role = role
        self.login_window = login_window

        self.setWindowTitle(f"App Nhot - Role: {role}")
        # Thiết lập kích thước cửa sổ
        self.resize(1600, 900)
        # Hiện full màn hình
        self.showMaximized()

        # Thiết lập layout chính
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Top bar
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        btn_doi_mk = QPushButton("Đổi mật khẩu")
        btn_doi_mk.clicked.connect(self.doi_mat_khau_click)
        top_bar.addWidget(btn_doi_mk)
        btn_dang_xuat = QPushButton("Đăng xuất")
        btn_dang_xuat.clicked.connect(self.dang_xuat)
        top_bar.addWidget(btn_dang_xuat)
        main_layout.addLayout(top_bar)

        # Tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        if self.role in ["accountant", "admin"]:
            self.tab_sanpham = QWidget()
            self.tabs.addTab(self.tab_sanpham, "San pham")
            self.init_tab_sanpham()

        self.tab_banhang = QWidget()
        self.tabs.addTab(self.tab_banhang, "Ban hang")
        self.init_tab_banhang()

        self.tab_chitietban = QWidget()
        self.tabs.addTab(self.tab_chitietban, "Chi tiet ban")
        self.init_tab_chitietban()

        self.tab_hoadon = QWidget()
        self.tabs.addTab(self.tab_hoadon, "Hoa don")
        self.init_tab_hoadon()

        self.tab_baocao = QWidget()
        self.tabs.addTab(self.tab_baocao, "Bao cao")
        self.init_tab_baocao()

        if self.role == "admin":
            self.tab_user = QWidget()
            self.tabs.addTab(self.tab_user, "Quan ly User")
            self.init_tab_user()

        if self.role == "accountant":
            self.tab_xuat_bo = QWidget()
            self.tabs.addTab(self.tab_xuat_bo, "Xuat bo")
            self.init_tab_xuat_bo()

            self.tab_cong_doan = QWidget()
            self.tabs.addTab(self.tab_cong_doan, "Cong doan")
            self.init_tab_cong_doan()

            self.tab_so_quy = QWidget()
            self.tabs.addTab(self.tab_so_quy, "So quy")
            self.init_tab_so_quy()

            # Tab nhận hàng cho mọi user
            self.tab_nhan_hang = QWidget()
            self.tabs.addTab(self.tab_nhan_hang, "Nhận hàng")
            self.init_tab_nhan_hang()

    def init_tab_nhan_hang(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Nhập số lượng sản phẩm đã nhận trong ca này:"))

        # Bảng nhập số lượng nhận
        self.tbl_nhan_hang = QTableWidget()
        self.tbl_nhan_hang.setColumnCount(3)
        self.tbl_nhan_hang.setHorizontalHeaderLabels(["Tên sản phẩm", "Số lượng nhận", "Ghi chú"])
        self.setup_table(self.tbl_nhan_hang)
        layout.addWidget(self.tbl_nhan_hang)

        # Nút tải danh sách sản phẩm
        btn_load_sp = QPushButton("Tải danh sách sản phẩm")
        btn_load_sp.clicked.connect(self.load_sanpham_nhan_hang)
        layout.addWidget(btn_load_sp)

        # Nút xác nhận nhận hàng
        btn_confirm = QPushButton("Xác nhận nhận hàng")
        btn_confirm.clicked.connect(self.xac_nhan_nhan_hang)
        layout.addWidget(btn_confirm)
        # Nút đóng ca
        btn_close_shift = QPushButton("Đóng ca (In tổng kết)")
        btn_close_shift.clicked.connect(self.dong_ca_in_pdf)
        layout.addWidget(btn_close_shift)
        self.tab_nhan_hang.setLayout(layout)

    def load_sanpham_nhan_hang(self):
        from products import lay_tat_ca_sanpham
        sp_list = lay_tat_ca_sanpham()
        self.tbl_nhan_hang.setRowCount(len(sp_list))
        for row, sp in enumerate(sp_list):
            self.tbl_nhan_hang.setItem(row, 0, QTableWidgetItem(sp[1]))  # Tên sản phẩm
            self.tbl_nhan_hang.setItem(row, 1, QTableWidgetItem("0"))   # Số lượng nhận
            self.tbl_nhan_hang.setItem(row, 2, QTableWidgetItem(""))   # Ghi chú

    def xac_nhan_nhan_hang(self):
        from datetime import datetime
        nhan_hang_data = []
        for row in range(self.tbl_nhan_hang.rowCount()):
            ten_sp = self.tbl_nhan_hang.item(row, 0).text()
            try:
                sl_nhan = float(self.tbl_nhan_hang.item(row, 1).text())
            except:
                sl_nhan = 0
            ghi_chu = self.tbl_nhan_hang.item(row, 2).text()
            nhan_hang_data.append((self.user_id, ten_sp, sl_nhan, ghi_chu, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        # Lưu vào DB hoặc file (tạm thời lưu file csv)
        import csv
        filename = f"nhan_hang_{self.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(filename, "w", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["user_id", "ten_sp", "so_luong_nhan", "ghi_chu", "thoi_gian"])
            writer.writerows(nhan_hang_data)
        QMessageBox.information(self, "Thành công", f"Đã lưu nhận hàng vào file {filename}")

        # Đảm bảo cửa sổ được hiển thị đúng cách
        self.show()

    def setup_table(self, table_widget):
        """Thiết lập bảng để hiển thị đầy đủ các cột"""
        # Tự động điều chỉnh độ rộng cột
        table_widget.horizontalHeader().setStretchLastSection(True)
        table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # Đảm bảo bảng có thể cuộn ngang nếu cần
        table_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        table_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    def tao_completer_sanpham(self):
        """Tạo QCompleter cho tên sản phẩm (tái sử dụng)"""
        ten_sanpham_list = lay_danh_sach_ten_sanpham()
        completer = QCompleter(ten_sanpham_list, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        return completer

    def cap_nhat_completer_sanpham(self):
        """Cập nhật lại completer cho tất cả các bảng sau khi thêm/xóa sản phẩm"""
        # Cập nhật cho tab bán hàng
        if hasattr(self, "tbl_giohang"):
            delegate = self.tbl_giohang.itemDelegateForColumn(0)
            if isinstance(delegate, CompleterDelegate):
                delegate.completer = self.tao_completer_sanpham()

    def init_tab_sanpham(self):
        layout = QVBoxLayout()
        self.tbl_sanpham = QTableWidget()
        self.tbl_sanpham.setColumnCount(7)
        self.tbl_sanpham.setHorizontalHeaderLabels(
            ["ID", "Tên", "Giá lẻ", "Giá buôn", "Giá VIP", "Tồn kho", "Ngưỡng buôn"]
        )
        self.setup_table(self.tbl_sanpham)
        self.tbl_sanpham.setEditTriggers(QTableWidget.DoubleClicked)
        self.tbl_sanpham.itemChanged.connect(self.update_product_price)
        layout.addWidget(self.tbl_sanpham)

        btn_layout = QHBoxLayout()
        btn_them = QPushButton("Thêm sản phẩm")
        btn_them.clicked.connect(self.them_sanpham_click)
        btn_layout.addWidget(btn_them)
        btn_nhap_kho = QPushButton("Nhập kho")
        btn_nhap_kho.clicked.connect(self.nhap_kho_click)
        btn_layout.addWidget(btn_nhap_kho)
        btn_xoa = QPushButton("Xóa sản phẩm")
        btn_xoa.clicked.connect(self.xoa_sanpham_click)
        btn_layout.addWidget(btn_xoa)
        btn_import = QPushButton("Import từ Excel")
        btn_import.clicked.connect(self.import_sanpham_excel)
        btn_layout.addWidget(btn_import)
        layout.addLayout(btn_layout)

        self.load_sanpham()
        self.tab_sanpham.setLayout(layout)

    def init_tab_banhang(self):
        layout = QVBoxLayout()

        # Bảng giỏ hàng
        self.tbl_giohang = QTableWidget()
        self.tbl_giohang.setColumnCount(8)
        self.tbl_giohang.setHorizontalHeaderLabels(
            ["Tên", "SL", "Đơn giá", "Giảm giá", "Tổng tiền", "VIP", "XHD", "Ghi chú"]
        )
        self.setup_table(self.tbl_giohang)
        self.tbl_giohang.setEditTriggers(QTableWidget.AllEditTriggers)
        # Tích hợp QCompleter cho cột Tên (cột 0)
        delegate = CompleterDelegate(self)
        delegate.completer = self.tao_completer_sanpham()
        self.tbl_giohang.setItemDelegateForColumn(0, delegate)
        # Kết nối signal itemChanged để xử lý thay đổi Tên và VIP
        self.tbl_giohang.itemChanged.connect(self.update_giohang)
        layout.addWidget(self.tbl_giohang)

        # Nút thêm dòng và tạo hóa đơn
        btn_layout = QHBoxLayout()
        btn_them_dong = QPushButton("Thêm dòng")
        btn_them_dong.clicked.connect(self.them_dong_giohang)
        btn_layout.addWidget(btn_them_dong)
        btn_tao_hd = QPushButton("Tạo hóa đơn")
        btn_tao_hd.clicked.connect(self.tao_hoa_don_click)
        btn_layout.addWidget(btn_tao_hd)
        layout.addLayout(btn_layout)

        self.tab_banhang.setLayout(layout)
        # Thêm 15 dòng rỗng ban đầu
        for _ in range(15):
            self.them_dong_giohang()

    def them_dong_giohang(self):
        row = self.tbl_giohang.rowCount()
        self.tbl_giohang.insertRow(row)
        # Khởi tạo các ô
        self.tbl_giohang.setItem(row, 0, QTableWidgetItem(""))  # Tên
        # Số lượng: QDoubleSpinBox cho số thực
        sl_spin = QDoubleSpinBox()
        sl_spin.setMinimum(0)
        sl_spin.setMaximum(9999)
        sl_spin.setDecimals(2)  # Cho phép 2 chữ số thập phân
        sl_spin.setValue(1.0)
        sl_spin.valueChanged.connect(lambda: self.update_giohang_row(row))
        self.tbl_giohang.setCellWidget(row, 1, sl_spin)  # SL
        self.tbl_giohang.setItem(row, 2, QTableWidgetItem(format_price(0)))  # Đơn giá
        # Giảm giá: QDoubleSpinBox cho số thực
        giam_spin = QDoubleSpinBox()
        giam_spin.setMinimum(0)
        giam_spin.setMaximum(999999)
        giam_spin.setDecimals(2)
        giam_spin.setValue(0)
        giam_spin.valueChanged.connect(lambda: self.update_giohang_row(row))
        self.tbl_giohang.setCellWidget(row, 3, giam_spin)  # Giảm giá
        self.tbl_giohang.setItem(row, 4, QTableWidgetItem(format_price(0)))  # Tổng tiền
        vip_item = QTableWidgetItem()
        vip_item.setCheckState(Qt.Unchecked)
        vip_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        self.tbl_giohang.setItem(row, 5, vip_item)  # VIP
        xhd_item = QTableWidgetItem()
        xhd_item.setCheckState(Qt.Unchecked)
        xhd_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        self.tbl_giohang.setItem(row, 6, xhd_item)  # XHD
        self.tbl_giohang.setItem(row, 7, QTableWidgetItem(""))  # Ghi chú
        print(f"Added row {row} with default values")  # Debug

    def update_giohang_row(self, row):
        print(f"Updating row {row}")  # Debug
        # Tạm disconnect signal để tránh vòng lặp
        self.tbl_giohang.itemChanged.disconnect(self.update_giohang)

        # Lấy dữ liệu dòng
        ten_item = self.tbl_giohang.item(row, 0)
        ten = ten_item.text().strip() if ten_item else ""
        print(f"Ten: {ten}")  # Debug
        sl_spin = self.tbl_giohang.cellWidget(row, 1)
        sl = sl_spin.value() if sl_spin else 1.0
        print(f"SL: {sl}")  # Debug
        don_gia_item = self.tbl_giohang.item(row, 2)
        don_gia = (
            float(don_gia_item.text().replace(",", ""))
            if don_gia_item and don_gia_item.text()
            else 0
        )
        print(f"Don gia (before update): {don_gia}")  # Debug
        giam_spin = self.tbl_giohang.cellWidget(row, 3)
        giam_gia = giam_spin.value() if giam_spin else 0
        print(f"Giam gia: {giam_gia}")  # Debug
        vip_item = self.tbl_giohang.item(row, 5)
        is_vip = vip_item.checkState() == Qt.Checked if vip_item else False
        print(f"Is VIP: {is_vip}")  # Debug

        # Cập nhật Đơn giá
        if ten:
            res = tim_sanpham(ten)
            print(f"tim_sanpham({ten}) result: {res}")  # Debug
            if res:
                sp = res[
                    0
                ]  # [id, ten, gia_le, gia_buon, gia_vip, ton_kho, nguong_buon]
                try:
                    nguong_buon = float(sp[6]) if sp[6] is not None else 0
                    if is_vip:
                        don_gia = float(sp[4])  # Giá VIP
                        print(f"Using gia_vip: {don_gia}")  # Debug
                    elif sl >= nguong_buon:  # Kiểm tra ngưỡng buôn
                        don_gia = float(sp[3])  # Giá buôn
                        print(
                            f"Using gia_buon: {don_gia} (SL={sl}, nguong_buon={nguong_buon})"
                        )  # Debug
                    else:
                        don_gia = float(sp[2])  # Giá lẻ
                        print(f"Using gia_le: {don_gia}")  # Debug
                    self.tbl_giohang.setItem(
                        row, 2, QTableWidgetItem(format_price(don_gia))
                    )
                except (ValueError, TypeError):
                    print(f"Invalid price data for product '{ten}'")  # Debug
                    # Reconnect signal trước khi return
                    self.tbl_giohang.itemChanged.connect(self.update_giohang)
                    return  # Không làm gì nếu dữ liệu giá không hợp lệ
            else:
                print(f"Sản phẩm '{ten}' không tồn tại")  # Debug
                self.tbl_giohang.setItem(row, 2, QTableWidgetItem(format_price(0)))
                don_gia = 0

        # Tính Tổng tiền
        try:
            tong_tien = sl * don_gia - giam_gia
            print(f"Tong tien: {tong_tien}")  # Debug
            self.tbl_giohang.setItem(row, 4, QTableWidgetItem(format_price(tong_tien)))
        except (ValueError, TypeError):
            print(f"Error calculating tong_tien for row {row}")  # Debug

            # Reconnect signal
        self.tbl_giohang.itemChanged.connect(self.update_giohang)

    def update_giohang(self, item):
        row = item.row()
        col = item.column()
        print(f"Item changed: row={row}, col={col}")  # Debug
        if col in [0, 5]:  # Chỉ xử lý khi thay đổi Tên hoặc VIP
            self.update_giohang_row(row)

    def tao_hoa_don_click(self):
        items = []
        for row in range(self.tbl_giohang.rowCount()):
            ten_item = self.tbl_giohang.item(row, 0)
            sl_spin = self.tbl_giohang.cellWidget(row, 1)
            don_gia_item = self.tbl_giohang.item(row, 2)
            giam_spin = self.tbl_giohang.cellWidget(row, 3)
            vip_item = self.tbl_giohang.item(row, 5)
            xhd_item = self.tbl_giohang.item(row, 6)
            ghi_chu_item = self.tbl_giohang.item(row, 7)

            # Bỏ qua dòng rỗng (nếu Tên rỗng)
            if not (ten_item and ten_item.text()):
                continue

            if not (sl_spin and don_gia_item):
                QMessageBox.warning(self, "Lỗi", f"Dòng {row+1} thiếu dữ liệu")
                return

            ten = ten_item.text().strip()
            res = tim_sanpham(ten)
            if not res:
                QMessageBox.warning(self, "Lỗi", f"Sản phẩm '{ten}' không tồn tại")
                return
            sanpham_id = res[0][0]
            so_luong = sl_spin.value() if sl_spin else 0
            try:
                gia = float(don_gia_item.text().replace(",", ""))
            except (ValueError, TypeError):
                QMessageBox.warning(self, "Lỗi", f"Giá không hợp lệ ở dòng {row+1}")
                return
            giam = giam_spin.value() if giam_spin else 0
            loai_gia = (
                "vip"
                if vip_item.checkState() == Qt.Checked
                else ("buon" if so_luong >= res[0][6] else "le")
            )
            xhd = xhd_item.checkState() == Qt.Checked
            ghi_chu = ghi_chu_item.text().strip() if ghi_chu_item else ""

            items.append(
                {
                    "sanpham_id": sanpham_id,
                    "so_luong": so_luong,
                    "loai_gia": loai_gia,
                    "gia": gia,
                    "giam": giam,
                    "xuat_hoa_don": xhd,
                    "ghi_chu": ghi_chu,
                }
            )

        if not items:
            QMessageBox.warning(self, "Lỗi", "Giỏ hàng rỗng")
            return

        print(f"Items before tao_hoa_don: {items}")
        try:
            khach_hang = ""
            uu_dai = 0
            xuat_hoa_don = 0
            giam_gia = 0
            success, msg, _ = tao_hoa_don(
                self.user_id, khach_hang, items, uu_dai, xuat_hoa_don, giam_gia
            )
        except Exception as e:
            print(f"Error calling tao_hoa_don: {str(e)}")
            QMessageBox.warning(self, "Lỗi", f"Lỗi gọi tao_hoa_don: {str(e)}")
            return

        if not success:
            print(f"tao_hoa_don failed: {msg}")
            QMessageBox.warning(self, "Lỗi", msg)
            return

        QMessageBox.information(
            self, "Thành công", f"Tạo hóa đơn thành công, ID: {msg}"
        )
        self.tbl_giohang.setRowCount(0)
        for _ in range(15):
            self.them_dong_giohang()

        if hasattr(self, "load_chitietban"):
            self.load_chitietban()

    def init_tab_chitietban(self):
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
                "Số dư",
                "Chi tiết",
                "Nộp tiền",
            ]
        )
        self.setup_table(self.tbl_chitietban)
        layout.addWidget(self.tbl_chitietban)

        btn_refresh = QPushButton("Làm mới")
        btn_refresh.clicked.connect(self.load_chitietban)
        layout.addWidget(btn_refresh)

        self.tab_chitietban.setLayout(layout)
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
            from datetime import datetime

            for hd in hoadons:
                try:
                    ngay_dt = datetime.strptime(hd[4], "%Y-%m-%d %H:%M:%S").date()
                except Exception:
                    # Nếu format khác, cố parse sơ bộ
                    try:
                        ngay_dt = datetime.fromisoformat(hd[4]).date()
                    except Exception:
                        # Nếu không parse được, giữ để tránh mất dữ liệu
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
            self.tbl_chitietban.setItem(
                row_idx, 1, QTableWidgetItem(str(hd[1]))
            )  # User ID
            self.tbl_chitietban.setItem(row_idx, 2, QTableWidgetItem(hd[2]))  # Username
            self.tbl_chitietban.setItem(row_idx, 3, QTableWidgetItem(hd[4]))  # Ngày
            self.tbl_chitietban.setItem(
                row_idx, 4, QTableWidgetItem(hd[5])
            )  # Trạng thái

            # Tính số dư = tổng tiền các sản phẩm CHƯA xuất hóa đơn (xuat_hoa_don=0)
            hoadon_id = hd[0]
            chi_tiet = lay_chi_tiet_hoadon(hoadon_id)
            unpaid_total = sum(
                row[4] * row[6] - row[9]  # so_luong * gia - giam
                for row in chi_tiet
                if row[7] == 0  # xuat_hoa_don == 0
            )

            # Lấy tổng đã nộp cho hóa đơn này (nếu GiaoDichQuy có trường hoadon_id)
            try:
                from users import lay_tong_nop_theo_hoadon

                paid = lay_tong_nop_theo_hoadon(hoadon_id)
            except Exception:
                paid = 0

            so_du = unpaid_total - (paid or 0)
            if so_du < 0:
                so_du = 0

            self.tbl_chitietban.setItem(
                row_idx, 5, QTableWidgetItem(format_price(so_du))
            )  # Số dư

            btn_detail = QPushButton("Chi tiết")
            btn_detail.clicked.connect(lambda checked, r=row_idx: self.xem_chi_tiet(r))
            self.tbl_chitietban.setCellWidget(row_idx, 6, btn_detail)
            # Tất cả user đều thấy nút "Nộp tiền"
            btn_nop = QPushButton("Nộp tiền")
            btn_nop.clicked.connect(lambda checked, r=row_idx: self.nop_tien(r))
            self.tbl_chitietban.setCellWidget(row_idx, 7, btn_nop)
        # Ẩn cột không cần hiển thị
        self.tbl_chitietban.setColumnHidden(0, True)  # ID
        self.tbl_chitietban.setColumnHidden(1, True)  # User ID
        self.tbl_chitietban.setColumnHidden(4, True)  # Trạng thái

    def xem_chi_tiet(self, row):
        hoadon_id = int(self.tbl_chitietban.item(row, 0).text())
        username = self.tbl_chitietban.item(row, 2).text()
        ngay = self.tbl_chitietban.item(row, 3).text()
        data = lay_chi_tiet_hoadon(hoadon_id)

        dialog = QDialog(self)
        dialog.setWindowTitle("Chi tiết hóa đơn")
        dialog.resize(800, 600)  # Tăng kích thước dialog
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
        for r_idx, row in enumerate(da_xuat):
            tbl_da.setItem(r_idx, 0, QTableWidgetItem(row[3]))  # ten
            tbl_da.setItem(r_idx, 1, QTableWidgetItem(str(row[4])))  # so_luong
            loai_gia_text = {"le": "Lẻ", "buon": "Buôn", "vip": "VIP"}.get(
                row[5], row[5]
            )
            tbl_da.setItem(r_idx, 2, QTableWidgetItem(loai_gia_text))  # loai_gia
            tbl_da.setItem(r_idx, 3, QTableWidgetItem(format_price(row[6])))  # gia
            tong = row[4] * row[6] - row[9]  # so_luong * gia - giam
            tbl_da.setItem(r_idx, 4, QTableWidgetItem(format_price(tong)))
            # Tính chênh lệch theo logic mới:
            # - XHĐ=1: chênh lệch = 0 (bất kể loại giá)
            # - Giá buôn: chênh lệch = 0
            # - Giá lẻ: chênh lệch = (giá_lẻ - giá_buôn) * số_lượng - giảm_giá
            if row[7] == 1:  # XHĐ=1 (bất kể loại giá)
                chenh = 0
            elif row[5] == "vip":  # VIP
                chenh = 0
            elif row[5] == "buon":  # Giá buôn
                chenh = 0
            elif row[5] == "le":  # Giá lẻ
                # Lấy giá buôn từ DB để tính chênh lệch
                from products import tim_sanpham

                sp_info = tim_sanpham(row[3])  # row[3] là tên sản phẩm
                if sp_info:
                    gia_buon = sp_info[0][3]  # gia_buon từ DB
                    chenh = (row[8] - gia_buon) * row[4] - row[
                        9
                    ]  # (gia_le - gia_buon) * so_luong - giam
                else:
                    chenh = 0
                # Debug: in ra giá trị để kiểm tra
                print(
                    f"DEBUG DA XUAT - SP: {row[3]}, gia_le: {row[8]}, gia_buon: {gia_buon if sp_info else 'N/A'}, sl: {row[4]}, giam: {row[9]}, chenh: {chenh}"
                )
            else:
                chenh = 0
            tbl_da.setItem(r_idx, 5, QTableWidgetItem(format_price(chenh)))
            ghi_chu = row[10] if len(row) > 10 else ""  # ghi_chu
            tbl_da.setItem(r_idx, 6, QTableWidgetItem(ghi_chu))
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
        for r_idx, row in enumerate(chua_xuat):
            tbl_chua.setItem(r_idx, 0, QTableWidgetItem(row[3]))  # ten
            tbl_chua.setItem(r_idx, 1, QTableWidgetItem(str(row[4])))  # so_luong
            loai_gia_text = {"le": "Lẻ", "buon": "Buôn", "vip": "VIP"}.get(
                row[5], row[5]
            )
            tbl_chua.setItem(r_idx, 2, QTableWidgetItem(loai_gia_text))  # loai_gia
            tbl_chua.setItem(r_idx, 3, QTableWidgetItem(format_price(row[6])))  # gia
            tong = row[4] * row[6] - row[9]  # so_luong * gia - giam
            tbl_chua.setItem(r_idx, 4, QTableWidgetItem(format_price(tong)))
            # Tính chênh lệch theo logic mới:
            # - XHĐ=1: chênh lệch = 0 (bất kể loại giá)
            # - Giá buôn: chênh lệch = 0
            # - Giá lẻ: chênh lệch = (giá_lẻ - giá_buôn) * số_lượng - giảm_giá
            if row[7] == 1:  # XHĐ=1 (bất kể loại giá)
                chenh = 0
            elif row[5] == "vip":  # VIP
                chenh = 0
            elif row[5] == "buon":  # Giá buôn
                chenh = 0
            elif row[5] == "le":  # Giá lẻ
                # Lấy giá buôn từ DB để tính chênh lệch
                from products import tim_sanpham

                sp_info = tim_sanpham(row[3])  # row[3] là tên sản phẩm
                if sp_info:
                    gia_buon = sp_info[0][3]  # gia_buon từ DB
                    chenh = (row[8] - gia_buon) * row[4] - row[
                        9
                    ]  # (gia_le - gia_buon) * so_luong - giam
                else:
                    chenh = 0
                # Debug: in ra giá trị để kiểm tra
                print(
                    f"DEBUG CHUA XUAT - SP: {row[3]}, gia_le: {row[8]}, gia_buon: {gia_buon if sp_info else 'N/A'}, sl: {row[4]}, giam: {row[9]}, chenh: {chenh}"
                )
            else:
                chenh = 0
            tbl_chua.setItem(r_idx, 5, QTableWidgetItem(format_price(chenh)))
            ghi_chu = row[10] if len(row) > 10 else ""  # ghi_chu
            tbl_chua.setItem(r_idx, 6, QTableWidgetItem(ghi_chu))
        layout.addWidget(tbl_chua)

        # Nút đóng
        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(dialog.close)
        layout.addWidget(btn_close)

        dialog.setLayout(layout)
        dialog.exec_()

    def nop_tien(self, row):
        # Lấy thông tin từ bảng (an toàn hơn vì có thể giá trị cell trống)
        try:
            hoadon_id = int(self.tbl_chitietban.item(row, 0).text())
        except Exception:
            QMessageBox.warning(self, "Lỗi", "Không lấy được ID hóa đơn")
            return
        try:
            user_id_from = int(self.tbl_chitietban.item(row, 1).text())
        except Exception:
            user_id_from = None
        username_from = self.tbl_chitietban.item(row, 2).text() if self.tbl_chitietban.item(row, 2) else ""

        # Tính số dư hiện tại từ DB: unpaid_total - paid
        from users import lay_tong_nop_theo_hoadon

        chi_tiet = lay_chi_tiet_hoadon(hoadon_id)
        unpaid_total = sum(
            (r[4] * r[6] - r[9]) for r in chi_tiet if r[7] == 0
        )
        try:
            paid = lay_tong_nop_theo_hoadon(hoadon_id)
        except Exception:
            paid = 0
        so_du_hien_tai = unpaid_total - (paid or 0)
        if so_du_hien_tai < 0:
            so_du_hien_tai = 0

        # Tìm user accountant để nhận tiền
        from users import lay_tat_ca_user

        users = lay_tat_ca_user()
        accountant_id = None
        accountant_username = None
        for user in users:
            if user[2] == "accountant":
                accountant_id = user[0]
                accountant_username = user[1]
                break

        if not accountant_id:
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy user accountant")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Nộp tiền")
        layout = QVBoxLayout()

        # Thông tin nộp tiền
        layout.addWidget(QLabel(f"PHIẾU NỘP TIỀN"))
        from datetime import datetime

        layout.addWidget(QLabel(f"Ngày: {datetime.now().strftime('%d/%m/%Y %H:%M')}"))
        layout.addWidget(QLabel(f"Từ: {username_from}"))
        layout.addWidget(QLabel(f"Đến: {accountant_username}"))
        layout.addWidget(QLabel(f"Số dư hiện tại: {format_price(so_du_hien_tai)}"))
        layout.addWidget(QLabel(""))

        # Nhập số tiền nộp
        tien_layout = QHBoxLayout()
        tien_layout.addWidget(QLabel("Số tiền nộp:"))
        so_tien_edit = QLineEdit()
        so_tien_edit.setPlaceholderText(
            f"Nhập số tiền (tối đa {format_price(so_du_hien_tai)})"
        )
        so_tien_edit.setText(str(int(so_du_hien_tai)))  # Mặc định nộp hết
        tien_layout.addWidget(so_tien_edit)
        layout.addLayout(tien_layout)

        # Đếm tờ tiền
        to_tien_layout = QVBoxLayout()
        to_tien_layout.addWidget(QLabel("Đếm tờ:"))
        menh_gia = [500000, 200000, 100000, 50000, 20000, 10000, 5000, 2000, 1000]
        self.to_tien_spins_nop_tien = []
        for mg in menh_gia:
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
        btn_confirm = QPushButton("Xác nhận nộp tiền")
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
        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(dialog.close)
        layout.addWidget(btn_close)

        dialog.setLayout(layout)
        dialog.exec_()

    def update_tong_to_tien_nop_tien(self):
        """Cập nhật tổng tiền từ số tờ trong nộp tiền"""
        tong = sum(spin.value() * mg for spin, mg in self.to_tien_spins_nop_tien)
        self.lbl_tong_to_nop_tien.setText(f"Tổng từ tờ: {format_price(tong)}")

    def xac_nhan_nop_tien(
        self, user_id_from, accountant_id, so_tien_str, so_du_hien_tai, dialog, row, hoadon_id=None
    ):
        """Xác nhận nộp tiền"""
        try:
            so_tien = float(so_tien_str.replace(",", ""))
            if so_tien <= 0:
                QMessageBox.warning(self, "Lỗi", "Số tiền phải lớn hơn 0")
                return
            if so_tien > so_du_hien_tai:
                QMessageBox.warning(
                    self,
                    "Lỗi",
                    f"Số tiền không được vượt quá số dư hiện tại ({format_price(so_du_hien_tai)})",
                )
                return

            # Chuyển tiền từ user sang accountant, kèm hoadon_id để dễ truy vết
            success, msg = chuyen_tien(user_id_from, accountant_id, so_tien, hoadon_id)
            if success:
                # Tính số dư còn lại
                so_du_con_lai = so_du_hien_tai - so_tien
                if so_du_con_lai == 0:
                    QMessageBox.information(
                        self,
                        "Thành công",
                        f"Nộp tiền thành công! Số dư về 0. Sản phẩm vẫn ở trạng thái chưa xuất hóa đơn.",
                    )
                else:
                    QMessageBox.information(
                        self,
                        "Thành công",
                        f"Nộp tiền thành công! Số dư còn lại: {format_price(so_du_con_lai)}. Sản phẩm vẫn ở trạng thái chưa xuất hóa đơn.",
                    )
                self.load_chitietban()  # Làm mới bảng
                try:
                    self.load_so_quy()  # Làm mới tab Sổ quỹ
                except Exception:
                    pass
                dialog.close()
            else:
                QMessageBox.warning(self, "Lỗi", f"Chuyển tiền thất bại: {msg}")
        except ValueError:
            QMessageBox.warning(self, "Lỗi", "Số tiền không hợp lệ")

    def in_phieu_thu(self, row):
        """In phiếu thu với số tờ các mệnh giá"""
        hoadon_id = int(self.tbl_chitietban.item(row, 0).text())
        user_id_from = int(self.tbl_chitietban.item(row, 1).text())
        username_from = self.tbl_chitietban.item(row, 2).text()
        so_tien = float(self.tbl_chitietban.item(row, 5).text().replace(",", ""))

        dialog = QDialog(self)
        dialog.setWindowTitle("In phiếu thu")
        layout = QVBoxLayout()

        # Thông tin phiếu thu
        layout.addWidget(QLabel(f"PHIẾU THU"))
        from datetime import datetime

        layout.addWidget(QLabel(f"Ngày: {datetime.now().strftime('%d/%m/%Y %H:%M')}"))
        layout.addWidget(QLabel(f"Từ: {username_from}"))
        layout.addWidget(QLabel(f"Số tiền: {format_price(so_tien)}"))
        layout.addWidget(QLabel(""))

        # Đếm tờ tiền
        to_tien_layout = QVBoxLayout()
        to_tien_layout.addWidget(QLabel("Đếm tờ:"))
        menh_gia = [500000, 200000, 100000, 50000, 20000, 10000, 5000, 2000, 1000]
        self.to_tien_spins_phieu_thu = []
        for mg in menh_gia:
            hl = QHBoxLayout()
            hl.addWidget(QLabel(format_price(mg)))
            spin = QSpinBox()
            spin.setMaximum(9999)
            spin.valueChanged.connect(
                lambda v, m=mg: self.update_tong_to_tien_phieu_thu()
            )
            hl.addWidget(spin)
            to_tien_layout.addLayout(hl)
            self.to_tien_spins_phieu_thu.append((spin, mg))
        layout.addLayout(to_tien_layout)
        self.lbl_tong_to_phieu_thu = QLabel("Tổng từ tờ: 0")
        layout.addWidget(self.lbl_tong_to_phieu_thu)

        # Nút in phiếu
        btn_print = QPushButton("In phiếu thu")
        btn_print.clicked.connect(lambda: self.in_phieu_thu_actual(dialog, row))
        layout.addWidget(btn_print)

        # Nút đóng
        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(dialog.close)
        layout.addWidget(btn_close)

        dialog.setLayout(layout)
        dialog.exec_()

    def update_tong_to_tien_phieu_thu(self):
        """Cập nhật tổng tiền từ số tờ trong phiếu thu"""
        tong = sum(spin.value() * mg for spin, mg in self.to_tien_spins_phieu_thu)
        self.lbl_tong_to_phieu_thu.setText(f"Tổng từ tờ: {format_price(tong)}")

    def in_phieu_thu_actual(self, dialog, row):
        """In phiếu thu thực tế"""
        printer = QPrinter()
        print_dialog = QPrintDialog(printer, self)
        if print_dialog.exec_() == QPrintDialog.Accepted:
            painter = QPainter()
            painter.begin(printer)

            # Lấy thông tin từ dialog
            so_tien = float(self.tbl_chitietban.item(row, 5).text().replace(",", ""))
            username_from = self.tbl_chitietban.item(row, 2).text()

            # Vẽ nội dung phiếu thu
            y = 50
            painter.drawText(100, y, "PHIẾU THU")
            y += 30
            from datetime import datetime

            painter.drawText(
                100, y, f"Ngày: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            )
            y += 30
            painter.drawText(100, y, f"Từ: {username_from}")
            y += 30
            painter.drawText(100, y, f"Số tiền: {format_price(so_tien)}")
            y += 50

            painter.drawText(100, y, "Đếm tờ:")
            y += 30

            # Vẽ số tờ các mệnh giá
            for spin, mg in self.to_tien_spins_phieu_thu:
                if spin.value() > 0:
                    painter.drawText(100, y, f"{format_price(mg)}: {spin.value()} tờ")
                    y += 25

            painter.end()
            QMessageBox.information(self, "Thành công", "In phiếu thu thành công!")
            dialog.close()

    def xem_chi_tiet_hoadon(self):
        try:
            hoadon_id = int(self.hoadon_id_edit.text())
            cts = lay_chi_tiet_hoadon(hoadon_id)
            self.tbl_chitietban.setRowCount(len(cts))
            for row_idx, ct in enumerate(cts):
                for col_idx, val in enumerate(ct):
                    if col_idx == 6:
                        val = format_price(val)
                    self.tbl_chitietban.setItem(
                        row_idx, col_idx, QTableWidgetItem(str(val))
                    )
        except:
            QMessageBox.warning(self, "Lỗi", "Hóa đơn ID không hợp lệ")

    def init_tab_hoadon(self):
        layout = QVBoxLayout()

        # Lọc theo ngày
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

        # Bảng sản phẩm đã XHĐ
        self.tbl_hoadon = QTableWidget()
        self.tbl_hoadon.setColumnCount(6)
        self.tbl_hoadon.setHorizontalHeaderLabels(
            ["Ngày", "Username", "Tên SP", "SL", "Loại giá", "Tổng tiền"]
        )
        self.setup_table(self.tbl_hoadon)
        layout.addWidget(self.tbl_hoadon)

        # Label tổng tiền
        self.lbl_tong_hoadon = QLabel("Tổng XHĐ: 0")
        self.lbl_tong_hoadon.setStyleSheet(
            "font-size: 14pt; font-weight: bold; color: blue;"
        )
        layout.addWidget(self.lbl_tong_hoadon)

        btn_export = QPushButton("Export Excel")
        btn_export.clicked.connect(self.export_hoadon_excel)
        layout.addWidget(btn_export)

        self.load_hoadon()
        self.tab_hoadon.setLayout(layout)

    def load_hoadon(self):
        tu_ngay = self.hoadon_tu_ngay.date().toString("yyyy-MM-dd")
        den_ngay = self.hoadon_den_ngay.date().toString("yyyy-MM-dd")

        # Load dữ liệu sản phẩm đã XHĐ
        from db import ket_noi

        try:
            conn = ket_noi()
            c = conn.cursor()

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

            # Nếu là staff thì chỉ xem hóa đơn của mình
            if self.role == "staff":
                sql += " AND hd.user_id = ?"
                params.append(self.user_id)

            # Lọc theo ngày
            if tu_ngay:
                sql += " AND date(hd.ngay) >= date(?)"
                params.append(tu_ngay)
            if den_ngay:
                sql += " AND date(hd.ngay) <= date(?)"
                params.append(den_ngay)

            sql += " ORDER BY hd.ngay DESC"

            c.execute(sql, params)
            data = c.fetchall()

            # Hiển thị dữ liệu
            self.tbl_hoadon.setRowCount(len(data))
            tong_tien = 0

            for row_idx, row in enumerate(data):
                ngay, username, ten_sp, so_luong, loai_gia, tong_tien_item = row

                # Chuyển đổi loại giá
                loai_gia_text = {"le": "Lẻ", "buon": "Buôn", "vip": "VIP"}.get(
                    loai_gia, loai_gia
                )

                self.tbl_hoadon.setItem(row_idx, 0, QTableWidgetItem(ngay))
                self.tbl_hoadon.setItem(row_idx, 1, QTableWidgetItem(username))
                self.tbl_hoadon.setItem(row_idx, 2, QTableWidgetItem(ten_sp))
                self.tbl_hoadon.setItem(row_idx, 3, QTableWidgetItem(str(so_luong)))
                self.tbl_hoadon.setItem(row_idx, 4, QTableWidgetItem(loai_gia_text))
                self.tbl_hoadon.setItem(
                    row_idx, 5, QTableWidgetItem(format_price(tong_tien_item))
                )

                tong_tien += tong_tien_item

            self.lbl_tong_hoadon.setText(f"Tổng XHĐ: {format_price(tong_tien)}")

        except Exception as e:
            print(f"Lỗi load XHD data: {e}")
        finally:
            conn.close()

    def export_hoadon_excel(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Lưu file Excel", "", "Excel Files (*.xlsx)"
        )
        if file_path:
            # Xuất dữ liệu đã xuất hóa đơn
            if export_hoa_don_excel(file_path, "Da_xuat"):
                QMessageBox.information(self, "Thành công", "Export thành công")

    def init_tab_baocao(self):
        layout = QVBoxLayout()
        
        # Tab widget để phân tách báo cáo kho và biểu đồ
        tab_widget = QTabWidget()
        
        # Tab báo cáo kho
        tab_kho = QWidget()
        kho_layout = QVBoxLayout()
        
        # Nút làm mới báo cáo kho
        btn_kho = QPushButton("Làm mới báo cáo kho")
        btn_kho.clicked.connect(self.xem_bao_cao_kho)
        kho_layout.addWidget(btn_kho)
        
        # Bảng báo cáo kho
        self.tbl_baocao_kho = QTableWidget()
        self.tbl_baocao_kho.setColumnCount(6)
        self.tbl_baocao_kho.setHorizontalHeaderLabels([
            "Tên sản phẩm", "Tồn kho", "Số lượng XHĐ", 
            "Số lượng xuất bổ", "Số lượng chưa xuất", "Trạng thái"
        ])
        # Thiết lập màu nền cho header
        self.tbl_baocao_kho.horizontalHeader().setStyleSheet(
            "QHeaderView::section { background-color: #D1E7FF; }"
        )
        self.setup_table(self.tbl_baocao_kho)
        kho_layout.addWidget(self.tbl_baocao_kho)
        
        tab_kho.setLayout(kho_layout)
        tab_widget.addTab(tab_kho, "Báo cáo kho")

        # Tab biểu đồ sản lượng
        tab_bieudo = QWidget()
        bieudo_layout = QVBoxLayout()
        
        # Controls cho biểu đồ
        filter_layout = QHBoxLayout()
        
        # Lọc theo năm
        filter_layout.addWidget(QLabel("Năm:"))
        self.bieudo_year = QComboBox()
        current_year = QDate.currentDate().year()
        self.bieudo_year.addItems([str(year) for year in range(current_year-5, current_year+1)])
        self.bieudo_year.setCurrentText(str(current_year))
        filter_layout.addWidget(self.bieudo_year)
        
        # Lọc theo tháng
        filter_layout.addWidget(QLabel("Tháng:"))
        self.bieudo_month = QComboBox()
        self.bieudo_month.addItems(['Tất cả'] + [str(m) for m in range(1, 13)])
        filter_layout.addWidget(self.bieudo_month)
        
        # Nút cập nhật biểu đồ
        btn_update = QPushButton("Cập nhật biểu đồ")
        btn_update.clicked.connect(self.cap_nhat_bieu_do)
        filter_layout.addWidget(btn_update)
        
        filter_layout.addStretch()
        bieudo_layout.addLayout(filter_layout)
        
        # Widget để chứa biểu đồ matplotlib
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
        from matplotlib.figure import Figure
        
        self.figure = Figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        bieudo_layout.addWidget(self.canvas)
        
        tab_bieudo.setLayout(bieudo_layout)
        tab_widget.addTab(tab_bieudo, "Biểu đồ sản lượng")
        
        layout.addWidget(tab_widget)
        self.tab_baocao.setLayout(layout)

    def xem_bao_cao_kho(self):
        try:
            conn = ket_noi()
            c = conn.cursor()
            
            # Lấy danh sách sản phẩm với tồn kho và ngưỡng buôn
            c.execute("SELECT id, ten, ton_kho, gia_buon, nguong_buon FROM SanPham ORDER BY ten")
            san_pham_list = c.fetchall()
            
            # Chuẩn bị data cho bảng
            table_data = []
            for sp in san_pham_list:
                sp_id, ten, ton_kho, _, nguong_buon = sp
                
                # Lấy số lượng đã xuất hóa đơn
                c.execute("""
                    SELECT COALESCE(SUM(so_luong), 0)
                    FROM ChiTietHoaDon 
                    WHERE sanpham_id = ? AND xuat_hoa_don = 1
                """, (sp_id,))
                sl_xhd = c.fetchone()[0] or 0
                
                # Lấy số lượng đã xuất bổ
                c.execute("""
                    SELECT COALESCE(SUM(so_luong), 0)
                    FROM LogKho 
                    WHERE sanpham_id = ? AND hanh_dong = 'xuat'
                """, (sp_id,))
                sl_xuat_bo = c.fetchone()[0] or 0
                
                # Lấy số lượng chưa xuất
                c.execute("""
                    SELECT COALESCE(SUM(so_luong), 0)
                    FROM ChiTietHoaDon 
                    WHERE sanpham_id = ? AND xuat_hoa_don = 0
                """, (sp_id,))
                sl_chua_xuat = c.fetchone()[0] or 0
                
                # Kiểm tra trạng thái tồn kho vs ngưỡng buôn
                trang_thai = ""
                if ton_kho < nguong_buon:
                    trang_thai = "⚠️ Dưới ngưỡng buôn"
                
                table_data.append([
                    ten, ton_kho, sl_xhd, sl_xuat_bo, sl_chua_xuat, trang_thai
                ])
            
            # Hiển thị dữ liệu
            self.tbl_baocao_kho.setRowCount(len(table_data))
            for row_idx, row_data in enumerate(table_data):
                for col_idx, val in enumerate(row_data):
                    item = QTableWidgetItem(str(val))
                    if col_idx == 5 and val:  # Cột trạng thái
                        item.setBackground(Qt.yellow)  # Highlight cảnh báo
                    self.tbl_baocao_kho.setItem(row_idx, col_idx, item)
                    
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Lỗi truy vấn dữ liệu: {str(e)}")
        finally:
            conn.close()

    def cap_nhat_bieu_do(self):
        try:
            conn = ket_noi()
            c = conn.cursor()
            
            nam = int(self.bieudo_year.currentText())
            thang = self.bieudo_month.currentText()
            
            # Xây dựng query với điều kiện lọc
            params = []
            date_filter = ""
            if thang != "Tất cả":
                date_filter = "AND strftime('%m', h.ngay) = ?"
                params.append(thang.zfill(2))
            
            # Query lấy sản lượng theo sản phẩm và thời gian
            sql = f"""
                SELECT 
                    s.ten,
                    strftime('%m', h.ngay) as thang,
                    SUM(c.so_luong) as tong_sl
                FROM ChiTietHoaDon c
                JOIN HoaDon h ON c.hoadon_id = h.id
                JOIN SanPham s ON c.sanpham_id = s.id
                WHERE strftime('%Y', h.ngay) = ?
                {date_filter}
                GROUP BY s.ten, strftime('%m', h.ngay)
                ORDER BY s.ten, thang
            """
            params.insert(0, str(nam))
            
            c.execute(sql, params)
            data = c.fetchall()
            
            # Chuẩn bị data cho biểu đồ
            products = sorted(list(set(row[0] for row in data)))
            months = sorted(list(set(row[1] for row in data)))
            
            # Tạo ma trận sản lượng
            quantities = {}
            for p in products:
                quantities[p] = [0] * len(months)
                for row in data:
                    if row[0] == p:
                        idx = months.index(row[1])
                        quantities[p][idx] = row[2]
            
            # Vẽ biểu đồ
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            x = range(len(months))
            width = 0.8 / len(products)
            
            for i, (product, qty) in enumerate(quantities.items()):
                ax.bar([xi + i*width for xi in x], qty, width, label=product)
            
            ax.set_xticks([xi + (len(products)-1)*width/2 for xi in x])
            ax.set_xticklabels([f'Tháng {m}' for m in months])
            
            ax.set_ylabel('Sản lượng')
            ax.set_title(f'Sản lượng theo sản phẩm năm {nam}' + 
                        (f' - Tháng {thang}' if thang != 'Tất cả' else ''))
            
            if len(products) > 1:
                ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            
            self.figure.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Lỗi vẽ biểu đồ: {str(e)}")
        finally:
            conn.close()

    def init_tab_user(self):
        layout = QVBoxLayout()
        self.tbl_user = QTableWidget()
        self.tbl_user.setColumnCount(4)
        self.tbl_user.setHorizontalHeaderLabels(["ID", "Username", "Role", "Số dư"])
        self.setup_table(self.tbl_user)
        layout.addWidget(self.tbl_user)

        btn_layout = QHBoxLayout()
        btn_them = QPushButton("Thêm user")
        btn_them.clicked.connect(self.them_user_click)
        btn_layout.addWidget(btn_them)
        btn_xoa = QPushButton("Xóa user")
        btn_xoa.clicked.connect(self.xoa_user_click)
        btn_layout.addWidget(btn_xoa)
        layout.addLayout(btn_layout)
        self.load_users()
        self.tab_user.setLayout(layout)

    def them_user_click(self):
        username, ok = QInputDialog.getText(self, "Thêm user", "Username:")
        if not ok:
            return
        password, ok = QInputDialog.getText(
            self, "Thêm user", "Password:", QLineEdit.Password
        )
        if not ok:
            return
        role, ok = QInputDialog.getItem(
            self, "Thêm user", "Role:", ["admin", "accountant", "staff"], 0
        )
        if ok:
            if them_user(username, password, role):
                QMessageBox.information(self, "Thành công", "Thêm user thành công")
                self.load_users()
            else:
                QMessageBox.warning(self, "Lỗi", "Thêm user thất bại")

    def xoa_user_click(self):
        row = self.tbl_user.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Lỗi", "Chọn một user")
            return
        user_id = int(self.tbl_user.item(row, 0).text())
        if user_id == self.user_id:
            QMessageBox.warning(self, "Lỗi", "Không thể xóa chính mình")
            return
        if xoa_user(user_id):
            QMessageBox.information(self, "Thành công", "Xóa user thành công")
            self.load_users()
        else:
            QMessageBox.warning(self, "Lỗi", "Xóa user thất bại")

    def load_users(self):
        users = lay_tat_ca_user()
        self.tbl_user.setRowCount(len(users))
        for row_idx, user in enumerate(users):
            for col_idx, val in enumerate(user):
                if col_idx == 3:
                    val = format_price(val)
                self.tbl_user.setItem(row_idx, col_idx, QTableWidgetItem(str(val)))

    def init_tab_xuat_bo(self):
        layout = QVBoxLayout()

        # Nút làm mới
        btn_refresh = QPushButton("Làm mới")
        btn_refresh.clicked.connect(self.load_xuatbo)
        layout.addWidget(btn_refresh)

        # 3 bảng ngang trong 1 hàng
        tables_layout = QHBoxLayout()

        # Bảng 1: Giá Buôn
        buon_layout = QVBoxLayout()
        buon_layout.addWidget(QLabel("CHƯA XUẤT - GIÁ BUÔN"))
        self.tbl_xuatbo_buon = QTableWidget()
        self.tbl_xuatbo_buon.setColumnCount(2)
        self.tbl_xuatbo_buon.setHorizontalHeaderLabels(["Tên sản phẩm", "Số lượng"])
        self.setup_table(self.tbl_xuatbo_buon)
        buon_layout.addWidget(self.tbl_xuatbo_buon)
        tables_layout.addLayout(buon_layout)

        # Bảng 2: Giá VIP
        vip_layout = QVBoxLayout()
        vip_layout.addWidget(QLabel("CHƯA XUẤT - GIÁ VIP"))
        self.tbl_xuatbo_vip = QTableWidget()
        self.tbl_xuatbo_vip.setColumnCount(2)
        self.tbl_xuatbo_vip.setHorizontalHeaderLabels(["Tên sản phẩm", "Số lượng"])
        self.setup_table(self.tbl_xuatbo_vip)
        vip_layout.addWidget(self.tbl_xuatbo_vip)
        tables_layout.addLayout(vip_layout)

        # Bảng 3: Giá Lẻ
        le_layout = QVBoxLayout()
        le_layout.addWidget(QLabel("CHƯA XUẤT - GIÁ LẺ"))
        self.tbl_xuatbo_le = QTableWidget()
        self.tbl_xuatbo_le.setColumnCount(3)
        self.tbl_xuatbo_le.setHorizontalHeaderLabels(
            ["Tên sản phẩm", "Số lượng", "Trạng thái"]
        )
        self.setup_table(self.tbl_xuatbo_le)
        le_layout.addWidget(self.tbl_xuatbo_le)
        tables_layout.addLayout(le_layout)

        layout.addLayout(tables_layout)

        # Footer: Form nhập xuất bổ
        layout.addWidget(QLabel("--- XUẤT BỔ THỦ CÔNG ---"))
        footer_layout = QVBoxLayout()

        # Danh sách các dòng nhập
        self.xuat_bo_rows = []
        self.xuat_bo_table = QTableWidget()
        self.xuat_bo_table.setColumnCount(4)
        self.xuat_bo_table.setHorizontalHeaderLabels(
            ["Tên sản phẩm", "Số lượng", "Loại giá", "Tiền"]
        )
        self.setup_table(self.xuat_bo_table)
        footer_layout.addWidget(self.xuat_bo_table)

        # Nút thêm dòng
        btn_them_dong = QPushButton("Thêm dòng")
        btn_them_dong.clicked.connect(self.them_dong_xuat_bo)
        footer_layout.addWidget(btn_them_dong)

        # Label tổng tiền
        self.lbl_tong_xuat_bo = QLabel("Tổng: 0")
        self.lbl_tong_xuat_bo.setStyleSheet("font-size: 14pt; font-weight: bold;")
        footer_layout.addWidget(self.lbl_tong_xuat_bo)

        # Nút xuất bổ
        btn_xuat_bo = QPushButton("XUẤT BỔ")
        btn_xuat_bo.clicked.connect(self.xuat_bo_click)
        btn_xuat_bo.setStyleSheet("font-size: 12pt; padding: 10px;")
        footer_layout.addWidget(btn_xuat_bo)

        layout.addLayout(footer_layout)

        self.load_xuatbo()
        # Thêm 5 dòng rỗng ban đầu
        for _ in range(5):
            self.them_dong_xuat_bo()

        self.tab_xuat_bo.setLayout(layout)

    def load_xuatbo(self):
        # Load bảng Buôn
        data_buon = lay_san_pham_chua_xuat_theo_loai_gia("buon")
        self.tbl_xuatbo_buon.setRowCount(len(data_buon))
        for row_idx, (ten, sl) in enumerate(data_buon):
            self.tbl_xuatbo_buon.setItem(row_idx, 0, QTableWidgetItem(ten))
            self.tbl_xuatbo_buon.setItem(row_idx, 1, QTableWidgetItem(str(sl)))

        # Load bảng VIP
        data_vip = lay_san_pham_chua_xuat_theo_loai_gia("vip")
        self.tbl_xuatbo_vip.setRowCount(len(data_vip))
        for row_idx, (ten, sl) in enumerate(data_vip):
            self.tbl_xuatbo_vip.setItem(row_idx, 0, QTableWidgetItem(ten))
            self.tbl_xuatbo_vip.setItem(row_idx, 1, QTableWidgetItem(str(sl)))

        # Load bảng Lẻ
        data_le = lay_san_pham_chua_xuat_theo_loai_gia("le")
        self.tbl_xuatbo_le.setRowCount(len(data_le))
        for row_idx, (ten, sl) in enumerate(data_le):
            self.tbl_xuatbo_le.setItem(row_idx, 0, QTableWidgetItem(ten))
            self.tbl_xuatbo_le.setItem(row_idx, 1, QTableWidgetItem(str(sl)))

            # Tính trạng thái: so sánh với ngưỡng buôn
            from products import tim_sanpham

            sp_info = tim_sanpham(ten)
            if sp_info:
                nguong_buon = sp_info[0][6] if len(sp_info[0]) > 6 else 0  # nguong_buon
                if sl >= nguong_buon:
                    trang_thai = "Có thể xuất"
                else:
                    trang_thai = "Chưa xuất được"
            else:
                trang_thai = "Không xác định"

            self.tbl_xuatbo_le.setItem(row_idx, 2, QTableWidgetItem(trang_thai))

    def them_dong_xuat_bo(self):
        row = self.xuat_bo_table.rowCount()
        self.xuat_bo_table.insertRow(row)

        # Cột Tên sản phẩm (với completer)
        ten_edit = QLineEdit()
        ten_edit.setCompleter(self.tao_completer_sanpham())
        ten_edit.textChanged.connect(lambda: self.update_xuat_bo_row(row))
        self.xuat_bo_table.setCellWidget(row, 0, ten_edit)

        # Cột Số lượng
        sl_spin = QDoubleSpinBox()
        sl_spin.setMinimum(0)
        sl_spin.setMaximum(9999)
        sl_spin.setDecimals(2)
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
                except:
                    pass
        self.lbl_tong_xuat_bo.setText(f"Tổng: {format_price(tong)}")

    def xuat_bo_click(self):
        # Lấy danh sách các dòng cần xuất
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

            sl = sl_spin.value()
            loai_gia = loai_gia_cb.currentText()

            items.append({"ten": ten, "so_luong": sl, "loai_gia": loai_gia})

        if not items:
            QMessageBox.warning(self, "Lỗi", "Không có sản phẩm để xuất")
            return

        # Kiểm tra số lượng có sẵn và tính chênh lệch công đoạn
        chenh_lech_total = 0
        chenh_lech_items = []

        for item in items:
            ten = item["ten"]
            sl_xuat = item["so_luong"]
            loai_gia_xuat = item["loai_gia"]

            # Lấy thông tin sản phẩm
            from products import tim_sanpham

            sp_info = tim_sanpham(ten)
            if not sp_info:
                QMessageBox.warning(self, "Lỗi", f"Sản phẩm '{ten}' không tồn tại")
                return

            sp = sp_info[0]
            gia_le = float(sp[2])
            gia_buon = float(sp[3])
            gia_vip = float(sp[4])

            # Lấy số lượng có sẵn từ các bảng
            sl_vip = self.get_sl_from_table("vip", ten)
            sl_buon = self.get_sl_from_table("buon", ten)
            sl_le = self.get_sl_from_table("le", ten)

            # Kiểm tra đủ số lượng và tính chênh lệch
            if loai_gia_xuat == "le":
                if sl_le < sl_xuat:
                    QMessageBox.warning(
                        self,
                        "Lỗi",
                        f"Sản phẩm '{ten}' không đủ số lượng giá lẻ (có {sl_le}, cần {sl_xuat})",
                    )
                    return
                # Giá lẻ không có chênh lệch công đoạn

            elif loai_gia_xuat == "buon":
                sl_can_tru = sl_xuat
                if sl_buon >= sl_can_tru:
                    # Đủ từ bảng buôn
                    pass
                else:
                    # Hỏi có lấy thêm từ bảng lẻ không
                    thieu = sl_can_tru - sl_buon
                    reply = QMessageBox.question(
                        self,
                        "Thiếu số lượng",
                        f"Giá buôn chỉ còn {sl_buon}. Cần lấy thêm {thieu} từ bảng giá lẻ?",
                        QMessageBox.Yes | QMessageBox.No,
                    )
                    if reply != QMessageBox.Yes:
                        return
                    if sl_le < thieu:
                        QMessageBox.warning(
                            self,
                            "Lỗi",
                            f"Sản phẩm '{ten}' không đủ số lượng (buôn: {sl_buon}, lẻ: {sl_le}, cần: {sl_xuat})",
                        )
                        return
                    # Lưu thông tin về loại giá phụ để xuất từ cả hai loại giá
                    item["loai_gia_phu"] = "le"
                    item["so_luong_phu"] = thieu

            elif loai_gia_xuat == "vip":
                sl_can_tru = sl_xuat
                # Trừ VIP trước
                sl_tru_vip = min(sl_can_tru, sl_vip)
                sl_can_tru -= sl_tru_vip

                # Sau đó trừ BUÔN
                sl_tru_buon = 0
                if sl_can_tru > 0 and sl_buon > 0:
                    sl_tru_buon = min(sl_can_tru, sl_buon)
                    sl_can_tru -= sl_tru_buon
                    # Lưu thông tin về loại giá phụ thứ 1 (buôn) để xuất từ cả ba loại giá
                    item["loai_gia_phu"] = "buon"
                    item["so_luong_phu"] = sl_tru_buon

                # Cuối cùng trừ LẺ
                sl_tru_le = 0
                if sl_can_tru > 0:
                    sl_tru_le = sl_can_tru
                    if sl_le < sl_tru_le:
                        QMessageBox.warning(
                            self,
                            "Lỗi",
                            f"Sản phẩm '{ten}' không đủ số lượng (VIP: {sl_vip}, buôn: {sl_buon}, lẻ: {sl_le}, cần: {sl_xuat})",
                        )
                        return
                    # Lưu thông tin về loại giá phụ thứ 2 (lẻ) để xuất từ cả ba loại giá
                    item["loai_gia_phu2"] = "le"
                    item["so_luong_phu2"] = sl_tru_le

                # Hiển thị thông báo xác nhận mượn cho giá VIP
                if sl_tru_buon > 0 or sl_tru_le > 0:
                    muon_text = f"Sản phẩm '{ten}' cần mượn:\n"
                    if sl_tru_buon > 0:
                        muon_text += f"- {sl_tru_buon} từ giá buôn\n"
                    if sl_tru_le > 0:
                        muon_text += f"- {sl_tru_le} từ giá lẻ\n"
                    muon_text += "\nXác nhận mượn?"
                    
                    reply = QMessageBox.question(
                        self,
                        "Xác nhận mượn",
                        muon_text,
                        QMessageBox.Yes | QMessageBox.No,
                    )
                    if reply != QMessageBox.Yes:
                        return

                # Tính chênh lệch công đoạn theo yêu cầu mới
                if sl_tru_buon > 0:
                    chenh_lech_items.append(
                        {
                            "ten": ten,
                            "sl": sl_tru_buon,
                            "gia_xuat": gia_vip,
                            "gia_goc": gia_buon,
                            "chenh_lech": gia_buon - gia_vip,  # (giá buôn - giá VIP)
                        }
                    )
                if sl_tru_le > 0:
                    chenh_lech_items.append(
                        {
                            "ten": ten,
                            "sl": sl_tru_le,
                            "gia_xuat": gia_vip,
                            "gia_goc": gia_le,
                            "chenh_lech": gia_le - gia_vip,  # (giá lẻ - giá VIP)
                        }
                    )

        # Hiển thị dialog chênh lệch công đoạn nếu có
        if chenh_lech_items:
            dialog = QDialog(self)
            dialog.setWindowTitle("Chênh lệch công đoạn")
            layout = QVBoxLayout()

            layout.addWidget(
                QLabel("Các sản phẩm cần điều chỉnh chênh lệch công đoạn:")
            )

            for item in chenh_lech_items:
                # Sử dụng chênh lệch đã tính sẵn theo công thức mới
                chenh_lech_item = item.get("chenh_lech", 0) * item["sl"]
                chenh_lech_total += chenh_lech_item
                layout.addWidget(
                    QLabel(
                        f"- {item['ten']}: {item['sl']} x {item.get('chenh_lech', 0)} = {format_price(chenh_lech_item)}"
                    )
                )

            layout.addWidget(
                QLabel(f"Tổng chênh lệch: {format_price(chenh_lech_total)}")
            )

            btn_ok = QPushButton("Xác nhận")
            btn_ok.clicked.connect(dialog.accept)
            layout.addWidget(btn_ok)

            dialog.setLayout(layout)
            if dialog.exec_() != QDialog.Accepted:
                return

        # Xuất từng sản phẩm
        errors = []
        for item in items:
            # Truyền thông tin về loại giá phụ nếu có
            loai_gia_phu = item.get("loai_gia_phu")
            so_luong_phu = item.get("so_luong_phu", 0)
            loai_gia_phu2 = item.get("loai_gia_phu2")
            so_luong_phu2 = item.get("so_luong_phu2", 0)

            # Tính chênh lệch cho từng phần
            sp_info = tim_sanpham(item["ten"])
            if not sp_info:
                errors.append(f"{item['ten']}: Không tìm thấy thông tin sản phẩm")
                continue
                
            sp = sp_info[0]
            gia_le = float(sp[2])
            gia_buon = float(sp[3])
            gia_vip = float(sp[4])

            # Với VIP, tính chênh lệch cho từng phần theo công thức mới
            if item["loai_gia"] == "vip":
                chenh_lech = 0  # Phần VIP không có chênh lệch
                chenh_buon = gia_buon - gia_vip  # (giá buôn - giá VIP) cho phần lấy từ giá buôn
                chenh_le = gia_le - gia_vip  # (giá lẻ - giá VIP) cho phần lấy từ giá lẻ
            else:
                # Với các loại giá khác, giữ nguyên logic cũ
                chenh_lech = chenh_lech_total

            # Tính chênh lệch phù hợp cho từng loại giá
            if item["loai_gia"] == "vip":
                # Với VIP, sử dụng chênh lệch đã tính cho từng phần
                chenh_lech_final = chenh_lech
            else:
                # Với các loại giá khác, sử dụng chênh lệch tổng
                chenh_lech_final = chenh_lech_total

            success, msg = xuat_bo_san_pham_theo_ten(
                item["ten"],
                item["loai_gia"],
                item["so_luong"],
                self.user_id,
                chenh_lech_final,
                loai_gia_phu,
                so_luong_phu,
                loai_gia_phu2,
                so_luong_phu2,
            )
            if not success:
                errors.append(f"{item['ten']}: {msg}")

        if errors:
            QMessageBox.warning(self, "Lỗi", "\n".join(errors))
        else:
            QMessageBox.information(self, "Thành công", "Xuất bổ thành công")

        # Làm mới
        self.load_xuatbo()
        self.xuat_bo_table.setRowCount(0)
        for _ in range(5):
            self.them_dong_xuat_bo()

    def get_sl_from_table(self, loai_gia, ten_sp):
        """Lấy số lượng từ bảng tương ứng"""
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

    def init_tab_cong_doan(self):
        layout = QVBoxLayout()

        # Lọc theo ngày (ô chọn ngày, không nhập tay)
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Từ ngày:"))
        self.tu_ngay_edit = QDateEdit()
        self.tu_ngay_edit.setCalendarPopup(True)  # Popup lịch để chọn
        self.tu_ngay_edit.setDate(
            QDate.currentDate().addMonths(-1)
        )  # Mặc định 1 tháng trước
        filter_layout.addWidget(self.tu_ngay_edit)

        filter_layout.addWidget(QLabel("Đến ngày:"))
        self.den_ngay_edit = QDateEdit()
        self.den_ngay_edit.setCalendarPopup(True)
        self.den_ngay_edit.setDate(QDate.currentDate())  # Mặc định hôm nay
        filter_layout.addWidget(self.den_ngay_edit)

        btn_load_cd = QPushButton("Tải báo cáo")
        btn_load_cd.clicked.connect(self.load_bao_cao_cong_doan)
        filter_layout.addWidget(btn_load_cd)

        layout.addLayout(filter_layout)

        self.tbl_cong_doan = QTableWidget()
        self.tbl_cong_doan.setColumnCount(6)
        self.tbl_cong_doan.setHorizontalHeaderLabels(
            ["ID", "SP ID", "User ID", "Ngày", "Số lượng", "Chênh lệch"]
        )
        self.setup_table(self.tbl_cong_doan)
        layout.addWidget(self.tbl_cong_doan)

        self.lbl_tong_cd = QLabel("Tổng: 0")
        layout.addWidget(self.lbl_tong_cd)

        self.tab_cong_doan.setLayout(layout)

    def load_bao_cao_cong_doan(self):
        tu_ngay = self.tu_ngay_edit.date().toString("yyyy-MM-dd")
        den_ngay = self.den_ngay_edit.date().toString("yyyy-MM-dd")
        data, tong = lay_bao_cao_cong_doan(tu_ngay, den_ngay)
        self.tbl_cong_doan.setRowCount(len(data))
        for row_idx, row in enumerate(data):
            for col_idx, val in enumerate(row):
                self.tbl_cong_doan.setItem(row_idx, col_idx, QTableWidgetItem(str(val)))
        self.lbl_tong_cd.setText(f"Tổng: {format_price(tong)}")

    def init_tab_so_quy(self):
        layout = QVBoxLayout()
        self.tbl_soquy = QTableWidget()
        self.tbl_soquy.setColumnCount(4)
        self.tbl_soquy.setHorizontalHeaderLabels(["ID", "Username", "Role", "Số dư"])
        self.setup_table(self.tbl_soquy)
        layout.addWidget(self.tbl_soquy)
        btn_refresh_quy = QPushButton("Làm mới")
        btn_refresh_quy.clicked.connect(self.load_so_quy)
        layout.addWidget(btn_refresh_quy)
        btn_chuyen_tien = QPushButton("Chuyển tiền")
        btn_chuyen_tien.clicked.connect(self.chuyen_tien_click)
        layout.addWidget(btn_chuyen_tien)
        self.tab_so_quy.setLayout(layout)
        self.load_so_quy()

    def load_so_quy(self):
        users = lay_tat_ca_user()
        self.tbl_soquy.setRowCount(len(users))
        for row_idx, user in enumerate(users):
            for col_idx, val in enumerate(user):
                if col_idx == 3:
                    val = format_price(val)
                self.tbl_soquy.setItem(row_idx, col_idx, QTableWidgetItem(str(val)))

    def chuyen_tien_click(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Chuyển tiền")
        layout = QVBoxLayout()

        # Lấy username của user hiện tại
        from users import lay_tat_ca_user

        users = lay_tat_ca_user()
        current_username = None
        for user in users:
            if user[0] == self.user_id:  # user[0] là ID
                current_username = user[1]  # user[1] là username
                break

        layout.addWidget(QLabel(f"Từ user: {current_username}"))
        layout.addWidget(QLabel("Đến user:"))

        # ComboBox chọn user
        den_user_combo = QComboBox()
        for user in users:
            if user[0] != self.user_id:  # Không hiển thị chính mình
                den_user_combo.addItem(
                    f"{user[1]} (ID: {user[0]})", user[0]
                )  # Hiển thị username, lưu ID
        layout.addWidget(den_user_combo)
        layout.addWidget(QLabel("Số tiền:"))
        so_tien_edit = QLineEdit()
        so_tien_edit.setValidator(QDoubleValidator())
        layout.addWidget(so_tien_edit)
        layout.addWidget(QLabel("Nội dung:"))
        noi_dung_edit = QLineEdit()
        noi_dung_edit.setPlaceholderText("Nhập lý do chuyển tiền...")
        layout.addWidget(noi_dung_edit)

        # Đếm tờ tiền
        to_tien_layout = QVBoxLayout()
        to_tien_layout.addWidget(QLabel("Đếm tờ:"))
        menh_gia = [500000, 200000, 100000, 50000, 20000, 10000, 5000, 2000, 1000]
        self.to_tien_spins = []
        for mg in menh_gia:
            hl = QHBoxLayout()
            hl.addWidget(QLabel(format_price(mg)))
            spin = QSpinBox()
            spin.setMaximum(9999)
            spin.valueChanged.connect(lambda v, m=mg: self.update_tong_to_tien())
            hl.addWidget(spin)
            to_tien_layout.addLayout(hl)
            self.to_tien_spins.append((spin, mg))
        layout.addLayout(to_tien_layout)
        self.lbl_tong_to = QLabel("Tổng từ tờ: 0")
        layout.addWidget(self.lbl_tong_to)

        btn_confirm = QPushButton("Xác nhận chuyển")
        btn_confirm.clicked.connect(
            lambda: self.xac_nhan_chuyen(
                den_user_combo.currentData(),
                so_tien_edit.text(),
                noi_dung_edit.text(),
                dialog,
            )
        )
        layout.addWidget(btn_confirm)
        btn_print = QPushButton("In phiếu")
        btn_print.clicked.connect(self.in_phieu_chuyen)
        layout.addWidget(btn_print)

        dialog.setLayout(layout)
        dialog.exec_()

    def update_tong_to_tien(self):
        tong = sum(spin.value() * mg for spin, mg in self.to_tien_spins)
        self.lbl_tong_to.setText(f"Tổng từ tờ: {format_price(tong)}")

    def xac_nhan_chuyen(self, den_id, so_tien, noi_dung, dialog):
        try:
            den_id = int(den_id)
            so_tien = float(so_tien)
            noi_dung = noi_dung.strip() if noi_dung else "Chuyển tiền"

            # Hiển thị thông tin xác nhận
            from users import lay_tat_ca_user

            users = lay_tat_ca_user()
            den_username = None
            for user in users:
                if user[0] == den_id:
                    den_username = user[1]
                    break

            reply = QMessageBox.question(
                self,
                "Xác nhận chuyển tiền",
                f"Chuyển {format_price(so_tien)} từ bạn đến {den_username}\nNội dung: {noi_dung}\n\nXác nhận?",
                QMessageBox.Yes | QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                success, msg = chuyen_tien(self.user_id, den_id, so_tien)
                if success:
                    QMessageBox.information(
                        self,
                        "Thành công",
                        f"Chuyển tiền thành công\nNội dung: {noi_dung}",
                    )
                    self.load_so_quy()
                    dialog.close()
                else:
                    QMessageBox.warning(self, "Lỗi", msg)
        except:
            QMessageBox.warning(self, "Lỗi", "Dữ liệu không hợp lệ")

    def in_phieu_chuyen(self):
        printer = QPrinter()
        dialog = QPrintDialog(printer, self)
        if dialog.exec_() != QPrintDialog.Accepted:
            return
        painter = QPainter(printer)
        painter.drawText(100, 100, "Phiếu chuyển tiền")
        painter.end()

    def doi_mat_khau_click(self):
        new_pwd, ok = QInputDialog.getText(
            self, "Đổi mật khẩu", "Mật khẩu mới", QLineEdit.Password
        )
        if ok:
            if doi_mat_khau(self.user_id, new_pwd):
                QMessageBox.information(self, "Thành công", "Đổi thành công")

    def dang_xuat(self):
        self.login_window.show()
        self.close()

    def load_sanpham(self):
        data = lay_tat_ca_sanpham()
        self.tbl_sanpham.setRowCount(len(data))
        for row_idx, sp in enumerate(data):
            for col_idx, val in enumerate(sp):
                if col_idx in [2, 3, 4]:
                    val = format_price(val)
                self.tbl_sanpham.setItem(row_idx, col_idx, QTableWidgetItem(str(val)))

    def them_sanpham_click(self):
        ten, ok = QInputDialog.getText(self, "Thêm sản phẩm", "Tên:")
        if not ok:
            return
        gia_le, ok = QInputDialog.getDouble(self, "Thêm sản phẩm", "Giá lẻ:")
        if not ok:
            return
        gia_buon, ok = QInputDialog.getDouble(self, "Thêm sản phẩm", "Giá buôn:")
        if not ok:
            return
        gia_vip, ok = QInputDialog.getDouble(self, "Thêm sản phẩm", "Giá VIP:")
        if not ok:
            return
        ton_kho, ok = QInputDialog.getInt(self, "Thêm sản phẩm", "Tồn kho:", 0)
        if not ok:
            return
        nguong_buon, ok = QInputDialog.getInt(self, "Thêm sản phẩm", "Ngưỡng buôn:", 0)
        if not ok:
            return
        if them_sanpham(ten, gia_le, gia_buon, gia_vip, ton_kho, nguong_buon):
            QMessageBox.information(self, "Thành công", "Thêm sản phẩm thành công")
            self.load_sanpham()
            # Cập nhật lại completer
            self.cap_nhat_completer_sanpham()
        else:
            QMessageBox.warning(self, "Lỗi", "Thêm sản phẩm thất bại")

    def nhap_kho_click(self):
        """Nhập kho sản phẩm (chỉ nhập tên và số lượng, giữ nguyên giá và ngưỡng buôn)"""
        # Dialog chọn sản phẩm
        ten_sanpham_list = lay_danh_sach_ten_sanpham()
        if not ten_sanpham_list:
            QMessageBox.warning(self, "Lỗi", "Chưa có sản phẩm nào trong hệ thống")
            return

        ten, ok = QInputDialog.getItem(
            self, "Nhập kho", "Chọn sản phẩm:", ten_sanpham_list, 0, False
        )
        if not ok or not ten:
            return

        # Nhập số lượng
        so_luong, ok = QInputDialog.getDouble(
            self, "Nhập kho", f"Số lượng nhập cho '{ten}':", 1, 0, 9999, 2
        )
        if not ok:
            return

        # Lấy thông tin sản phẩm hiện tại
        res = tim_sanpham(ten)
        if not res:
            QMessageBox.warning(self, "Lỗi", f"Sản phẩm '{ten}' không tồn tại")
            return

        sp = res[0]  # [id, ten, gia_le, gia_buon, gia_vip, ton_kho, nguong_buon]
        gia_le = sp[2]
        gia_buon = sp[3]
        gia_vip = sp[4]
        ton_kho_cu = sp[5]
        nguong_buon = sp[6]

        # Thêm sản phẩm (hàm them_sanpham sẽ tự cộng số lượng vào tồn kho)
        if them_sanpham(ten, gia_le, gia_buon, gia_vip, so_luong, nguong_buon):
            ton_kho_moi = ton_kho_cu + so_luong
            QMessageBox.information(
                self,
                "Thành công",
                f"Nhập kho thành công!\nSản phẩm: {ten}\nSố lượng nhập: {so_luong}\nTồn kho cũ: {ton_kho_cu}\nTồn kho mới: {ton_kho_moi}",
            )
            self.load_sanpham()
        else:
            QMessageBox.warning(self, "Lỗi", "Nhập kho thất bại")

    def xoa_sanpham_click(self):
        row = self.tbl_sanpham.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Lỗi", "Chọn một sản phẩm")
            return
        ten_sp = self.tbl_sanpham.item(row, 1).text()
        if xoa_sanpham(ten_sp):
            QMessageBox.information(self, "Thành công", "Xóa sản phẩm thành công")
            self.load_sanpham()
            # Cập nhật lại completer
            self.cap_nhat_completer_sanpham()
        else:
            QMessageBox.warning(self, "Lỗi", "Xóa sản phẩm thất bại")

    def update_product_price(self, item):
        row = item.row()
        col = item.column()
        if col not in [
            2,
            3,
            4,
            5,
        ]:  # Chỉ cho phép chỉnh sửa giá lẻ, giá buôn, giá VIP, tồn kho
            return
        try:
            product_id = int(self.tbl_sanpham.item(row, 0).text())
            value = float(item.text().replace(",", ""))
            field = ["gia_le", "gia_buon", "gia_vip", "ton_kho"][col - 2]
            conn = ket_noi()
            c = conn.cursor()
            c.execute(f"UPDATE SanPham SET {field}=? WHERE id=?", (value, product_id))
            conn.commit()
            conn.close()
        except:
            QMessageBox.warning(self, "Lỗi", "Giá trị không hợp lệ")

    def import_sanpham_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Chọn file Excel", "", "Excel Files (*.xlsx)"
        )
        if file_path:
            try:
                df = pd.read_excel(file_path)
                if import_sanpham_from_dataframe(df):
                    QMessageBox.information(
                        self, "Thành công", "Import sản phẩm thành công"
                    )
                    self.load_sanpham()
                    # Cập nhật lại completer
                    self.cap_nhat_completer_sanpham()
                else:
                    QMessageBox.warning(self, "Lỗi", "Import sản phẩm thất bại")
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", f"Lỗi import: {str(e)}")

    def dong_ca_in_pdf(self):
        from datetime import datetime
        from PyQt5.QtPrintSupport import QPrinter
        from PyQt5.QtGui import QPainter
        # Lấy dữ liệu nhận hàng
        nhan_hang_data = []
        for row in range(self.tbl_nhan_hang.rowCount()):
            ten_sp = self.tbl_nhan_hang.item(row, 0).text()
            try:
                sl_nhan = float(self.tbl_nhan_hang.item(row, 1).text())
            except:
                sl_nhan = 0
            ghi_chu = self.tbl_nhan_hang.item(row, 2).text()
            nhan_hang_data.append((ten_sp, sl_nhan, ghi_chu))

        # Lấy dữ liệu bán hàng (giả sử lấy từ bảng chi tiết hóa đơn của user trong ngày)
        today = datetime.now().strftime('%Y-%m-%d')
        from invoices import lay_danh_sach_hoadon, lay_chi_tiet_hoadon
        hoadons = lay_danh_sach_hoadon("Da_xuat")
        tong_tien = 0
        tong_cong_doan = 0
        tong_nop = 0
        tong_thieu = 0
        sp_ban_list = []
        for hd in hoadons:
            if hd[1] == self.user_id and hd[4][:10] == today:
                chi_tiet = lay_chi_tiet_hoadon(hd[0])
                for r in chi_tiet:
                    sp_ban_list.append((r[3], r[4], r[6]))  # tên, sl, giá
                    tong_tien += r[4]*r[6] - r[9]
        # Lấy công đoàn
        from stock import lay_bao_cao_cong_doan
        _, tong_cong_doan = lay_bao_cao_cong_doan(today, today)
        # Lấy tiền đã nộp
        from users import lay_tong_nop_theo_hoadon
        for hd in hoadons:
            if hd[1] == self.user_id and hd[4][:10] == today:
                tong_nop += lay_tong_nop_theo_hoadon(hd[0]) or 0
        tong_thieu = tong_tien - tong_nop

        # Tạo file PDF
        filename = f"tong_ket_ca_{self.user_id}_{today}.pdf"
        printer = QPrinter()
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(filename)
        painter = QPainter()
        painter.begin(printer)
        y = 50
        painter.drawText(100, y, f"TỔNG KẾT CA BÁN HÀNG - User: {self.user_id} - Ngày: {today}")
        y += 40
        painter.drawText(100, y, "--- Sản phẩm nhận ---")
        y += 30
        for ten_sp, sl_nhan, ghi_chu in nhan_hang_data:
            painter.drawText(120, y, f"{ten_sp}: {sl_nhan} ({ghi_chu})")
            y += 25
        y += 20
        painter.drawText(100, y, "--- Sản phẩm đã bán ---")
        y += 30
        for ten, sl, gia in sp_ban_list:
            painter.drawText(120, y, f"{ten}: {sl} x {gia}")
            y += 25
        y += 20
        painter.drawText(100, y, f"Tổng tiền bán: {tong_tien}")
        y += 25
        painter.drawText(100, y, f"Chênh lệch công đoàn: {tong_cong_doan}")
        y += 25
        painter.drawText(100, y, f"Tiền đã nộp: {tong_nop}")
        y += 25
        painter.drawText(100, y, f"Tiền còn thiếu: {tong_thieu}")
        y += 40
        painter.drawText(100, y, "--- Kết thúc ca ---")
        painter.end()
        QMessageBox.information(self, "Thành công", f"Đã in tổng kết ca vào file {filename}")
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = DangNhap()
    win.show()
    sys.exit(app.exec_())