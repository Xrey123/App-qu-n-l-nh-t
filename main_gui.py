import sys
import pandas as pd
import os
import csv
from datetime import datetime, timedelta
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
    QDateTimeEdit,
    QDialog,
    QTextEdit,
    QDialogButtonBox,
    QDoubleSpinBox,
    QStyledItemDelegate,
    QHeaderView,
)
from PyQt5.QtCore import Qt, QDate, QDateTime
from PyQt5.QtGui import QIcon, QPixmap

from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtGui import QPainter, QDoubleValidator

# Helpers
from utils.money import MENH_GIA
from utils.invoice import (
    tinh_unpaid_total,
    chon_don_gia,
    xac_dinh_loai_gia,
    tinh_chenh_lech,
)
from utils.ui_helpers import (
    show_error,
    show_info,
    show_success,
    show_warning,
    show_confirmation,
    setup_quantity_spinbox,
)

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
    except Exception as e:
        print(f"Warning: Error formatting price {value}: {e}")
        return str(value)


# ✅ Hàm quản lý thư mục lưu trữ file
def tao_thu_muc_luu_tru():
    """Tạo thư mục để lưu file nhận hàng và tổng kết ca"""
    base_dir = os.path.dirname(__file__)
    data_dir = os.path.join(base_dir, "data_export")
    nhan_hang_dir = os.path.join(data_dir, "nhan_hang")
    tong_ket_dir = os.path.join(data_dir, "tong_ket_ca")

    # Tạo các thư mục nếu chưa tồn tại
    os.makedirs(nhan_hang_dir, exist_ok=True)
    os.makedirs(tong_ket_dir, exist_ok=True)

    return nhan_hang_dir, tong_ket_dir


def xoa_file_cu(thu_muc, so_thang=3):
    """Xóa các file cũ hơn số tháng chỉ định trong thư mục"""
    try:
        ngay_hien_tai = datetime.now()
        so_ngay = so_thang * 30  # Tương đương số tháng

        for filename in os.listdir(thu_muc):
            filepath = os.path.join(thu_muc, filename)

            # Chỉ xóa file, không xóa thư mục
            if os.path.isfile(filepath):
                # Lấy thời gian sửa đổi file
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))

                # Tính số ngày từ file đến hiện tại
                so_ngay_cu = (ngay_hien_tai - file_time).days

                # Xóa nếu file cũ hơn số tháng chỉ định
                if so_ngay_cu > so_ngay:
                    os.remove(filepath)
                    print(f"Đã xóa file cũ: {filename} ({so_ngay_cu} ngày)")
    except Exception as e:
        print(f"Lỗi khi xóa file cũ: {e}")


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
        self.setWindowTitle("Đăng nhập")

        # ✅ Set Window Icon cho cửa sổ đăng nhập
        try:
            import os

            logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
            if os.path.exists(logo_path):
                self.setWindowIcon(QIcon(logo_path))
        except Exception as e:
            print(f"Không thể load logo: {e}")

        self.resize(380, 480)

        # === CLEAN MODERN LOGIN DESIGN ===
        self.setStyleSheet(
            """
            QWidget { background: white; font-family: Arial; }
            QLabel { color: black; font-size: 10pt; }
            QLineEdit { font-size: 10pt; background: white; color: black; border: 1px solid #ccc; border-radius: 2px; padding: 4px; }
            QPushButton { font-size: 10pt; background: #e0e0e0; color: black; border: 1px solid #ccc; border-radius: 2px; padding: 6px 12px; }
            QPushButton:hover { background: #d0d0d0; }
        """
        )

        # Main container
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(0)

        card = QWidget()
        card.setMaximumWidth(340)
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(12)

        # Logo
        try:
            logo_label = QLabel()
            logo_pixmap = QPixmap(logo_path)
            logo_scaled = logo_pixmap.scaled(
                100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            logo_label.setPixmap(logo_scaled)
            logo_label.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(logo_label)
        except Exception as e:
            print(f"Không thể hiển thị logo: {e}")

        # Username field
        self.user_edit = QLineEdit()
        self.user_edit.setPlaceholderText("Tên đăng nhập")
        card_layout.addWidget(self.user_edit)

        card_layout.addSpacing(12)

        # Password field
        self.pwd_edit = QLineEdit()
        self.pwd_edit.setEchoMode(QLineEdit.Password)
        self.pwd_edit.setPlaceholderText("Mật khẩu")
        card_layout.addWidget(self.pwd_edit)

        card_layout.addSpacing(16)

        # Login button
        btn = QPushButton("ĐĂNG NHẬP")
        btn.clicked.connect(self.dang_nhap_click)
        btn.setCursor(Qt.PointingHandCursor)
        card_layout.addWidget(btn)

    # Footer text (ẩn hoặc để trống)
    # footer = QLabel("")
    # card_layout.addWidget(footer)

        card.setLayout(card_layout)

        # Center card in window
        h_layout = QHBoxLayout()
        h_layout.addStretch()
        h_layout.addWidget(card)
        h_layout.addStretch()

        main_layout.addStretch()
        main_layout.addLayout(h_layout)
        main_layout.addStretch()

        self.setLayout(main_layout)

    def dang_nhap_click(self):
        username = self.user_edit.text().strip()
        pwd = self.pwd_edit.text().strip()
        user = dang_nhap(username, pwd)
        if not user:
            show_error(self, "Lỗi", "Sai tài khoản hoặc mật khẩu")
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
        self.last_invoice_id = None  # Lưu ID hóa đơn mới nhất trong ca

        # Lấy username từ database
        from users import lay_tat_ca_user

        self.username = "User"
        try:
            users = lay_tat_ca_user()
            for u in users:
                if u[0] == user_id:
                    self.username = u[1]
                    break
        except Exception as e:
            print(f"Warning: Could not load username for user_id {user_id}: {e}")

        self.setWindowTitle(f"Hệ thống quản lý bán hàng")

        # ✅ Set Window Icon (logo trên title bar và taskbar)
        try:
            import os

            logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
            if os.path.exists(logo_path):
                self.setWindowIcon(QIcon(logo_path))
        except Exception as e:
            print(f"Không thể load logo: {e}")

        # Thiết lập kích thước cửa sổ
        self.resize(1600, 900)
        # Hiện full màn hình
        self.showMaximized()

        # Xóa theme màu — dùng giao diện mặc định của hệ điều hành
        self.setStyleSheet("")

        # Thiết lập layout chính
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        self.setLayout(main_layout)

        # Top bar với lời chào
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        # ✅ Hiển thị lời chào username
        greeting = QLabel(f"Xin chào, {self.username}")
        top_bar.addWidget(greeting)

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

        # In-memory map of products available for sale in this session.
        # Keys: product name, value: total received quantity (float)
        self.available_products = {}

        # Track whether user has completed receiving products
        self.nhan_hang_completed = False
        # Track whether shift is closed
        self.ca_closed = False

        if self.role in ["accountant", "admin"]:
            self.tab_sanpham = QWidget()
            self.tabs.addTab(self.tab_sanpham, "Sản phẩm")
            self.init_tab_sanpham()

            self.tab_lich_su_gia = QWidget()
            self.tabs.addTab(self.tab_lich_su_gia, "Lịch sử giá")
            self.init_tab_lich_su_gia()

        # Create a parent tab "Ca bán hàng" which contains two child tabs:
        # - "Bán hàng" (where products can be sold)
        # - "Nhận hàng" (where users record received items)
        self.tab_ca_banhang = QWidget()
        ca_layout = QVBoxLayout()
        self.tab_ca_banhang_tabs = QTabWidget()
        ca_layout.addWidget(self.tab_ca_banhang_tabs)
        self.tab_ca_banhang.setLayout(ca_layout)
        self.tabs.addTab(self.tab_ca_banhang, "Ca bán hàng")

        # Child tab: Nhận hàng - make available to all users (not only accountant)
        self.tab_nhan_hang = QWidget()
        self.tab_ca_banhang_tabs.addTab(self.tab_nhan_hang, "Nhận hàng")
        self.init_tab_nhan_hang()

        # Child tab: Bán hàng
        self.tab_banhang = QWidget()
        self.tab_ca_banhang_tabs.addTab(self.tab_banhang, "Bán hàng")
        self.init_tab_banhang()

        # Other top-level tabs
        self.tab_chitietban = QWidget()
        self.tabs.addTab(self.tab_chitietban, "Chi tiết bán")
        self.init_tab_chitietban()

        self.tab_hoadon = QWidget()
        self.tabs.addTab(self.tab_hoadon, "Hóa đơn")
        self.init_tab_hoadon()

        self.tab_baocao = QWidget()
        self.tabs.addTab(self.tab_baocao, "Báo cáo")
        self.init_tab_baocao()

        if self.role == "admin":
            self.tab_user = QWidget()
            self.tabs.addTab(self.tab_user, "Quản lý User")
            self.init_tab_user()

        # Tab chênh lệch cho admin và accountant
        if self.role in ["admin", "accountant"]:
            self.tab_chenhlech = QWidget()
            self.tabs.addTab(self.tab_chenhlech, "Chênh lệch")
            self.init_tab_chenhlech()

        if self.role == "accountant":
            self.tab_xuat_bo = QWidget()
            self.tabs.addTab(self.tab_xuat_bo, "Xuất bổ")
            self.init_tab_xuat_bo()

            self.tab_cong_doan = QWidget()
            self.tabs.addTab(self.tab_cong_doan, "Công đoàn")
            self.init_tab_cong_doan()

            self.tab_so_quy = QWidget()
            self.tabs.addTab(self.tab_so_quy, "Sổ quỹ")
            self.init_tab_so_quy()

            self.tab_nhap_dau_ky = QWidget()
            self.tabs.addTab(self.tab_nhap_dau_ky, "Nhập đầu kỳ")
            self.init_tab_nhap_dau_ky()

    def init_tab_nhan_hang(self):
        layout = QVBoxLayout()
        layout.addWidget(
            QLabel("Kiểm kê / Nhập số lượng hiện có (so sánh với tồn hệ thống):")
        )

        # Bảng nhập số lượng kiểm kê
        self.tbl_nhan_hang = QTableWidget()
        # Columns: Tên, Số lượng đếm, Tồn hệ thống, Chênh lệch, Ghi chú
        self.tbl_nhan_hang.setColumnCount(5)
        self.tbl_nhan_hang.setHorizontalHeaderLabels(
            ["Tên sản phẩm", "Số lượng đếm", "Tồn hệ thống", "Chênh lệch", "Ghi chú"]
        )
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
        self.tab_nhan_hang.setLayout(layout)

    def load_sanpham_nhan_hang(self):
        from products import lay_tat_ca_sanpham

        sp_list = lay_tat_ca_sanpham()
        self.tbl_nhan_hang.setRowCount(len(sp_list))
        for row, sp in enumerate(sp_list):
            # sp = (id, ten, gia_le, gia_buon, gia_vip, ton_kho, nguong_buon)
            ten = sp[1]
            ton_db = sp[5] if len(sp) > 5 and sp[5] is not None else 0
            self.tbl_nhan_hang.setItem(row, 0, QTableWidgetItem(ten))
            # Prefill counted quantity with system stock to make counting easier
            self.tbl_nhan_hang.setItem(row, 1, QTableWidgetItem(str(ton_db)))
            # Show system stock
            self.tbl_nhan_hang.setItem(row, 2, QTableWidgetItem(str(ton_db)))
            # Chênh lệch = counted - system (start at 0)
            self.tbl_nhan_hang.setItem(row, 3, QTableWidgetItem(str(0)))
            # Ghi chú
            self.tbl_nhan_hang.setItem(row, 4, QTableWidgetItem(""))

            # ✅ CẬP NHẬT available_products từ DB mới nhất (bao gồm cả số lượng đã bán)
            # Điều này đảm bảo sau khi đóng ca, tải lại danh sách sẽ thấy tồn kho đã trừ đi hàng bán
            self.available_products[ten] = ton_db

    def xac_nhan_nhan_hang(self):
        from datetime import datetime

        nhan_hang_data = []
        discrepancies = []
        for row in range(self.tbl_nhan_hang.rowCount()):
            ten_item = self.tbl_nhan_hang.item(row, 0)
            if not ten_item:
                continue
            ten_sp = ten_item.text()
            try:
                sl_dem = float(self.tbl_nhan_hang.item(row, 1).text())
            except Exception:
                sl_dem = 0
            try:
                ton_db = float(self.tbl_nhan_hang.item(row, 2).text())
            except Exception:
                ton_db = 0
            ghi_chu = (
                self.tbl_nhan_hang.item(row, 4).text()
                if self.tbl_nhan_hang.item(row, 4)
                else ""
            )
            chenh = sl_dem - ton_db
            # update chênh lệch cell
            # show integer when whole number
            if float(chenh).is_integer():
                ch_text = str(int(chenh))
            else:
                ch_text = str(chenh)
            self.tbl_nhan_hang.setItem(row, 3, QTableWidgetItem(ch_text))
            nhan_hang_data.append(
                (
                    self.user_id,
                    ten_sp,
                    sl_dem,
                    ton_db,
                    chenh,
                    ghi_chu,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                )
            )
            if abs(chenh) >= 1e-9 and chenh != 0:
                status = "DƯ" if chenh > 0 else "THIẾU"
                discrepancies.append((ten_sp, chenh, status))

        # ✅ Lưu file nhận hàng vào thư mục riêng và xóa file cũ
        nhan_hang_dir, _ = tao_thu_muc_luu_tru()
        xoa_file_cu(nhan_hang_dir, so_thang=3)  # Xóa file cũ hơn 3 tháng

        filename = (
            f"nhan_hang_{self.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        filepath = os.path.join(nhan_hang_dir, filename)

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "user_id",
                    "ten_sp",
                    "so_luong_dem",
                    "ton_db",
                    "chenh_lech",
                    "ghi_chu",
                    "thoi_gian",
                ]
            )
            writer.writerows(nhan_hang_data)

        # Report results to user
        if discrepancies:
            # Build a detailed dialog to allow user to select which discrepancies to apply
            dlg = QDialog(self)
            dlg.setWindowTitle("Xác nhận chênh lệch kho")
            dlg.resize(800, 400)
            dlg_layout = QVBoxLayout()
            info_lbl = QLabel(
                f"Phát hiện chênh lệch ({len(discrepancies)} sản phẩm). Chọn những mục muốn áp vào kho và nhập lý do (bắt buộc khi có chênh lệch)."
            )
            dlg_layout.addWidget(info_lbl)

            tbl = QTableWidget()
            tbl.setColumnCount(5)
            tbl.setHorizontalHeaderLabels(
                [
                    "Chọn",
                    "Sản phẩm",
                    "Tồn hệ thống",
                    "Chênh lệch",
                    "Ghi chú lý do (bắt buộc)",
                ]
            )
            tbl.setRowCount(len(discrepancies))
            for i, (ten_sp, chenh, status) in enumerate(discrepancies):
                chk = QTableWidgetItem()
                chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                chk.setCheckState(Qt.Checked)
                tbl.setItem(i, 0, chk)
                tbl.setItem(i, 1, QTableWidgetItem(ten_sp))
                # find ton_db from nhan_hang_data
                ton_db = 0
                for rec in nhan_hang_data:
                    if rec[1] == ten_sp:
                        ton_db = rec[3]
                        break
                # show ton system
                tbl.setItem(i, 2, QTableWidgetItem(str(ton_db)))
                tbl.setItem(
                    i,
                    3,
                    QTableWidgetItem(
                        str(int(chenh) if float(chenh).is_integer() else chenh)
                    ),
                )
                # Reason (mandatory)
                tbl.setItem(i, 4, QTableWidgetItem(""))

            tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            dlg_layout.addWidget(tbl)

            btns = QHBoxLayout()
            apply_btn = QPushButton("Áp chênh lệch vào kho")
            cancel_btn = QPushButton("Hủy")
            btns.addWidget(apply_btn)
            btns.addWidget(cancel_btn)
            dlg_layout.addLayout(btns)
            dlg.setLayout(dlg_layout)

            def on_cancel():
                dlg.reject()

            def on_apply():
                # Collect selected rows and ensure reasons provided
                to_apply = []  # list of (ten_sp, chenh, reason)
                for r in range(tbl.rowCount()):
                    item_chk = tbl.item(r, 0)
                    if item_chk and item_chk.checkState() == Qt.Checked:
                        ten = tbl.item(r, 1).text()
                        ch = float(tbl.item(r, 3).text())
                        reason_item = tbl.item(r, 4)
                        reason = reason_item.text().strip() if reason_item else ""
                        if not reason:
                            show_error(
                                dlg,
                                "Lỗi",
                                f"Vui lòng nhập lý do cho sản phẩm {ten} trước khi áp.",
                            )
                            return
                        to_apply.append((ten, ch, reason))

                if not to_apply:
                    show_info(
                        dlg, "Thông báo", "Không có mục nào được chọn để áp."
                    )
                    return

                # Apply changes to DB: update SanPham.ton_kho = counted (ton_sau), insert into LogKho and ChenhLech
                conn = ket_noi()
                c = conn.cursor()
                try:
                    for ten, ch, reason in to_apply:
                        # Get product id and current stock
                        c.execute(
                            "SELECT id, ton_kho FROM SanPham WHERE ten = ?", (ten,)
                        )
                        row = c.fetchone()
                        if not row:
                            show_error(
                                dlg, "Lỗi", f"Không tìm thấy sản phẩm {ten} trong DB"
                            )
                            conn.rollback()
                            return
                        sp_id, ton_truoc = row
                        # Find counted qty from nhan_hang_data
                        counted = None
                        for rec in nhan_hang_data:
                            if rec[1] == ten:
                                counted = rec[2]
                                break
                        if counted is None:
                            counted = ton_truoc + ch

                        ton_sau = counted

                        # Update SanPham.ton_kho
                        c.execute(
                            "UPDATE SanPham SET ton_kho = ? WHERE id = ?",
                            (ton_sau, sp_id),
                        )

                        # Insert into LogKho (hanh_dong = 'kiemke')
                        ngay = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        c.execute(
                            "INSERT INTO LogKho (sanpham_id, user_id, ngay, hanh_dong, so_luong, ton_truoc, ton_sau, gia_ap_dung, chenh_lech_cong_doan) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (
                                sp_id,
                                self.user_id,
                                ngay,
                                "kiemke",
                                ch,
                                ton_truoc,
                                ton_sau,
                                0,
                                ch,
                            ),
                        )

                        # Insert into ChenhLech table
                        c.execute(
                            "INSERT INTO ChenhLech (sanpham_id, user_id, ngay, chenh, ton_truoc, ton_sau, ghi_chu) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (sp_id, self.user_id, ngay, ch, ton_truoc, ton_sau, reason),
                        )

                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    show_error(dlg, "Lỗi", f"Lỗi khi cập nhật DB: {e}")
                    conn.close()
                    return
                conn.close()

                # Update in-memory baseline
                for ten, ch, reason in to_apply:
                    # set available_products to new counted value
                    # find counted
                    counted = None
                    for rec in nhan_hang_data:
                        if rec[1] == ten:
                            counted = rec[2]
                            break
                    if counted is None:
                        counted = 0
                    self.available_products[ten] = counted

                self.cap_nhat_completer_sanpham()
                show_success(
                    dlg, "Đã áp chênh lệch vào kho và ghi log."
                )
                dlg.accept()

            apply_btn.clicked.connect(on_apply)
            cancel_btn.clicked.connect(on_cancel)

            dialog_result = dlg.exec_()
            if dialog_result != QDialog.Accepted:
                # User cancelled — do not proceed with receiving
                show_info(
                    self,
                    "Hủy nhận hàng",
                    "Bạn đã hủy. Vui lòng sửa số liệu và nhấn 'Xác nhận nhận hàng' lại.",
                )
                return
        else:
            show_info(
                self, "Kiểm kê", "Không có chênh lệch. Đã lưu kết quả kiểm kê."
            )

        # Update in-memory available_products based on counted quantities so selling uses counted baseline
        for rec in nhan_hang_data:
            _, ten_sp, sl_dem, ton_db, chenh, ghi_chu, thoi_gian = rec
            try:
                q = float(sl_dem)
            except Exception:
                q = 0
            self.available_products[ten_sp] = q

        # Refresh completer used in Bán hàng
        self.cap_nhat_completer_sanpham()

        # Mark receiving as completed and disable the tab
        self.nhan_hang_completed = True
        self.tab_nhan_hang.setEnabled(False)

        # ✅ Mở lại tab Bán hàng và reset trạng thái ca
        self.ca_closed = False
        self.tab_banhang.setEnabled(True)

        # Enable the 'Lưu' button in Bán hàng so user can save/create invoices
        try:
            self.btn_luu.setEnabled(True)
        except Exception:
            pass
        show_success(
            self,
            "Đã nhận hàng thành công. Tab Nhận hàng sẽ bị khóa, Tab Bán hàng đã mở.\nBạn có thể bắt đầu bán hàng.",
        )

        self.show()

    def setup_table(self, table_widget):
        """Thiết lập bảng để hiển thị đầy đủ các cột"""
        # Tự động điều chỉnh độ rộng cột
        table_widget.horizontalHeader().setStretchLastSection(True)
        table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # Đảm bảo bảng có thể cuộn ngang nếu cần
        table_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        table_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # Không dùng màu nền thay thế — giữ mặc định
        table_widget.setAlternatingRowColors(False)
        # Tăng chiều cao dòng mặc định để nội dung dễ nhìn hơn
        try:
            table_widget.verticalHeader().setDefaultSectionSize(26)  # giảm từ 30
        except Exception:
            pass

    def create_section_label(self, text, icon=""):
        """Tạo label header đơn giản, không icon, không màu nền"""
        return QLabel(text)

    def tao_completer_sanpham(self):
        """Tạo QCompleter cho tên sản phẩm (tái sử dụng).

        If available_only is True, only return names present in self.available_products
        with quantity > 0. Otherwise return the full product name list from DB.
        """

        def _make(names):
            comp = QCompleter(names, self)
            comp.setCaseSensitivity(Qt.CaseInsensitive)
            comp.setFilterMode(Qt.MatchContains)
            return comp

        # Default: full list
        ten_sanpham_list = lay_danh_sach_ten_sanpham()
        return _make(ten_sanpham_list)

    def sys_baocao_by_ten(self, ten_sanpham: str) -> float:
        """
        Tính SYS theo đúng logic hiển thị ở tab Báo cáo cho 1 sản phẩm (theo tên):
        SYS = Tồn kho hiện tại + Số lượng chưa xuất (CTHD xuat_hoa_don=0 + DauKyXuatBo)

        Trả về 0 nếu không tìm thấy sản phẩm hoặc có lỗi.
        """
        try:
            ten = (ten_sanpham or "").strip()
            if not ten:
                return 0
            conn = ket_noi()
            c = conn.cursor()
            c.execute("SELECT id, ton_kho FROM SanPham WHERE ten=?", (ten,))
            row = c.fetchone()
            if not row:
                conn.close()
                return 0
            sp_id, ton_kho = row[0], float(row[1] or 0)

            # Số lượng bán chưa xuất hóa đơn
            try:
                c.execute(
                    """
                    SELECT COALESCE(SUM(so_luong), 0)
                    FROM ChiTietHoaDon
                    WHERE sanpham_id = ? AND xuat_hoa_don = 0
                    """,
                    (sp_id,),
                )
                sl_chua_xuat_cthd = float(c.fetchone()[0] or 0)
            except Exception:
                sl_chua_xuat_cthd = 0.0

            # Đầu kỳ còn lại
            try:
                c.execute(
                    """
                    SELECT COALESCE(SUM(so_luong), 0)
                    FROM DauKyXuatBo
                    WHERE sanpham_id = ?
                    """,
                    (sp_id,),
                )
                sl_dau_ky = float(c.fetchone()[0] or 0)
            except Exception:
                sl_dau_ky = 0.0

            conn.close()
            sl_chua_xuat = sl_chua_xuat_cthd + sl_dau_ky
            return ton_kho + sl_chua_xuat
        except Exception:
            try:
                conn.close()
            except Exception:
                pass
            return 0

    def cap_nhat_completer_sanpham(self):
        """Cập nhật lại completer cho tất cả các bảng sau khi thêm/xóa sản phẩm"""
        # Cập nhật cho tab bán hàng
        if hasattr(self, "tbl_giohang"):
            delegate = self.tbl_giohang.itemDelegateForColumn(0)
            if isinstance(delegate, CompleterDelegate):
                # Build a completer that only suggests products that are available
                # for sale (received quantity > 0). If no received products yet,
                # provide an empty completer so no suggestions appear.
                available_names = [
                    name for name, qty in self.available_products.items() if qty > 0
                ]
                if available_names:
                    comp = QCompleter(available_names, self)
                    comp.setCaseSensitivity(Qt.CaseInsensitive)
                    comp.setFilterMode(Qt.MatchContains)
                    delegate.completer = comp
                else:
                    delegate.completer = QCompleter([], self)

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
        btn_layout.addStretch()
        btn_them = QPushButton("Thêm sản phẩm")
        btn_them.clicked.connect(self.them_sanpham_click)
        btn_layout.addWidget(btn_them)
        btn_nhap_kho = QPushButton("Nhập kho")
        btn_nhap_kho.clicked.connect(self.nhap_kho_click)
        btn_layout.addWidget(btn_nhap_kho)
        btn_xoa = QPushButton("Xóa sản phẩm")
        btn_xoa.clicked.connect(self.xoa_sanpham_click)
        btn_layout.addWidget(btn_xoa)
        btn_import = QPushButton("Import Excel")
        btn_import.clicked.connect(self.import_sanpham_excel)
        btn_layout.addWidget(btn_import)
        layout.addLayout(btn_layout)

        self.load_sanpham()
        self.tab_sanpham.setLayout(layout)

    def init_tab_lich_su_gia(self):
        """Tab để xem lịch sử thay đổi giá - hiển thị theo ngày với 3 loại giá"""
        layout = QVBoxLayout()

        # Hướng dẫn sử dụng
        info_label = QLabel(
            "💡 Cách thay đổi giá:\n"
            "1. Tab Sản phẩm: Double-click vào ô giá để sửa từng sản phẩm\n"
            "2. Tab Sản phẩm: Nhấn 'Import Excel' để cập nhật giá hàng loạt"
        )
        info_label.setStyleSheet("background-color: #fff3cd; padding: 10px; border-radius: 5px;")
        layout.addWidget(info_label)

        # Bộ lọc - chỉ còn lọc theo ngày
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Từ ngày:"))
        self.lich_su_gia_tu = QDateEdit()
        self.lich_su_gia_tu.setCalendarPopup(True)
        self.lich_su_gia_tu.setDate(QDate.currentDate().addMonths(-1))
        filter_layout.addWidget(self.lich_su_gia_tu)
        
        filter_layout.addWidget(QLabel("Đến ngày:"))
        self.lich_su_gia_den = QDateEdit()
        self.lich_su_gia_den.setCalendarPopup(True)
        self.lich_su_gia_den.setDate(QDate.currentDate())
        filter_layout.addWidget(self.lich_su_gia_den)

        btn_load_lich_su = QPushButton("Tải dữ liệu")
        btn_load_lich_su.clicked.connect(self.load_lich_su_gia)
        filter_layout.addWidget(btn_load_lich_su)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # TreeWidget cho lịch sử (dòng cha: ngày, dòng con: sản phẩm)
        from PyQt5.QtWidgets import QTreeWidget
        self.tree_lich_su_gia = QTreeWidget()
        self.tree_lich_su_gia.setHeaderLabels([
            "Ngày/Sản phẩm", "Lẻ cũ", "Lẻ mới", "Buôn cũ", "Buôn mới", "VIP cũ", "VIP mới", "User"
        ])
        self.tree_lich_su_gia.setAlternatingRowColors(True)
        layout.addWidget(self.tree_lich_su_gia)

        # Label tổng số thay đổi
        self.lbl_tong_lich_su = QLabel("Tổng số sản phẩm: 0")
        layout.addWidget(self.lbl_tong_lich_su)

        self.tab_lich_su_gia.setLayout(layout)
        self.load_lich_su_gia()

    def load_lich_su_gia(self):
        """Load dữ liệu lịch sử thay đổi giá - hiển thị TẤT CẢ sản phẩm"""
        from PyQt5.QtWidgets import QTreeWidgetItem
        from collections import defaultdict
        
        try:
            conn = ket_noi()
            c = conn.cursor()
            
            tu_ngay = self.lich_su_gia_tu.date().toString("yyyy-MM-dd")
            den_ngay = self.lich_su_gia_den.date().toString("yyyy-MM-dd")

            # 1. Lấy TẤT CẢ sản phẩm hiện có
            c.execute("SELECT id, ten, gia_le, gia_buon, gia_vip FROM SanPham ORDER BY ten")
            all_products = c.fetchall()
            
            # 2. Lấy lịch sử thay đổi giá trong khoảng thời gian
            sql = """
                SELECT 
                    date(ls.ngay_thay_doi) as ngay,
                    ls.ten_sanpham, 
                    ls.loai_gia,
                    ls.gia_cu, 
                    ls.gia_moi,
                    u.username
                FROM LichSuGia ls
                LEFT JOIN Users u ON ls.user_id = u.id
                WHERE date(ls.ngay_thay_doi) >= ? AND date(ls.ngay_thay_doi) <= ?
                ORDER BY ls.ngay_thay_doi DESC, ls.ten_sanpham
            """
            c.execute(sql, [tu_ngay, den_ngay])
            history_rows = c.fetchall()

            self.tree_lich_su_gia.clear()

            # 3. Nhóm lịch sử theo (ngày, sản phẩm, loại giá)
            history_groups = defaultdict(lambda: defaultdict(dict))
            for ngay, ten_sp, loai_gia, gia_cu, gia_moi, username in history_rows:
                history_groups[ngay][ten_sp][loai_gia] = {
                    'gia_cu': gia_cu,
                    'gia_moi': gia_moi,
                    'username': username
                }

            # 4. Tạo dict để tra cứu giá hiện tại
            current_prices = {}
            for sp_id, ten, gia_le, gia_buon, gia_vip in all_products:
                current_prices[ten] = {
                    'le': gia_le,
                    'buon': gia_buon,
                    'vip': gia_vip
                }

            tong_san_pham = len(all_products)
            
            if history_groups:
                # Có lịch sử thay đổi - hiển thị theo ngày
                for ngay in sorted(history_groups.keys(), reverse=True):
                    # Tạo dòng cha cho ngày
                    parent = QTreeWidgetItem(self.tree_lich_su_gia)
                    parent.setText(0, ngay)
                    font = parent.font(0)
                    font.setBold(True)
                    parent.setFont(0, font)
                    
                    # Tạo dòng con cho từng sản phẩm trong ngày này
                    for ten_sp in sorted(history_groups[ngay].keys()):
                        data = history_groups[ngay][ten_sp]
                        
                        child = QTreeWidgetItem(parent)
                        child.setText(0, ten_sp)
                        
                        # Lẻ
                        if 'le' in data:
                            child.setText(1, format_price(data['le']['gia_cu']))
                            child.setText(2, format_price(data['le']['gia_moi']))
                        elif ten_sp in current_prices:
                            # Chưa thay đổi giá lẻ → hiển thị giá hiện tại
                            gia = current_prices[ten_sp]['le']
                            child.setText(1, format_price(gia))
                            child.setText(2, format_price(gia))
                        
                        # Buôn
                        if 'buon' in data:
                            child.setText(3, format_price(data['buon']['gia_cu']))
                            child.setText(4, format_price(data['buon']['gia_moi']))
                        elif ten_sp in current_prices:
                            gia = current_prices[ten_sp]['buon']
                            child.setText(3, format_price(gia))
                            child.setText(4, format_price(gia))
                        
                        # VIP
                        if 'vip' in data:
                            child.setText(5, format_price(data['vip']['gia_cu']))
                            child.setText(6, format_price(data['vip']['gia_moi']))
                        elif ten_sp in current_prices:
                            gia = current_prices[ten_sp]['vip']
                            child.setText(5, format_price(gia))
                            child.setText(6, format_price(gia))
                        
                        # User
                        username = ""
                        for loai in ['le', 'buon', 'vip']:
                            if loai in data:
                                username = data[loai]['username'] or ""
                                break
                        child.setText(7, username)
                    
                    parent.setExpanded(True)
            else:
                # Không có lịch sử → hiển thị TẤT CẢ sản phẩm với giá hiện tại
                parent = QTreeWidgetItem(self.tree_lich_su_gia)
                parent.setText(0, "Giá hiện tại (chưa có thay đổi)")
                font = parent.font(0)
                font.setBold(True)
                parent.setFont(0, font)
                
                for sp_id, ten, gia_le, gia_buon, gia_vip in all_products:
                    child = QTreeWidgetItem(parent)
                    child.setText(0, ten)
                    # Giá cũ = Giá mới (chưa thay đổi)
                    child.setText(1, format_price(gia_le))
                    child.setText(2, format_price(gia_le))
                    child.setText(3, format_price(gia_buon))
                    child.setText(4, format_price(gia_buon))
                    child.setText(5, format_price(gia_vip))
                    child.setText(6, format_price(gia_vip))
                    child.setText(7, "")
                
                parent.setExpanded(True)

            self.lbl_tong_lich_su.setText(f"Tổng số sản phẩm: {tong_san_pham}")
            
            for i in range(8):
                self.tree_lich_su_gia.resizeColumnToContents(i)

            conn.close()
        except Exception as e:
            show_error(self, "Lỗi", f"Không thể tải lịch sử giá: {e}")

    def init_tab_chenhlech(self):
        layout = QVBoxLayout()

        # Filters
        fl = QHBoxLayout()
        fl.addWidget(QLabel("Từ ngày:"))
        self.chenh_tu = QDateEdit()
        self.chenh_tu.setCalendarPopup(True)
        self.chenh_tu.setDate(QDate.currentDate().addMonths(-1))
        fl.addWidget(self.chenh_tu)
        fl.addWidget(QLabel("Đến ngày:"))
        self.chenh_den = QDateEdit()
        self.chenh_den.setCalendarPopup(True)
        self.chenh_den.setDate(QDate.currentDate())
        fl.addWidget(self.chenh_den)
        btn_load = QPushButton("Tải dữ liệu")
        btn_load.clicked.connect(self.load_chenhlech)
        fl.addWidget(btn_load)
        fl.addStretch()
        layout.addLayout(fl)

        self.tbl_chenhlech = QTableWidget()
        self.tbl_chenhlech.setColumnCount(7)
        self.tbl_chenhlech.setHorizontalHeaderLabels(
            ["Ngày", "Sản phẩm", "Chênh", "Tồn trước", "Tồn sau", "Ghi chú", "Xử lý"]
        )
        self.setup_table(self.tbl_chenhlech)
        layout.addWidget(self.tbl_chenhlech)

        # Thêm nút xử lý chênh lệch (góc phải)
        btn_layout_chenh = QHBoxLayout()
        btn_layout_chenh.addStretch()
        btn_xu_ly_chenh = QPushButton("Xử lý chênh lệch")
        btn_xu_ly_chenh.clicked.connect(self.xu_ly_chenh_lech_click)
        btn_layout_chenh.addWidget(btn_xu_ly_chenh)
        layout.addLayout(btn_layout_chenh)

        self.tab_chenhlech.setLayout(layout)
        self.load_chenhlech()

    def load_chenhlech(self):
        try:
            conn = ket_noi()
            c = conn.cursor()
            tu = self.chenh_tu.date().toString("yyyy-MM-dd")
            den = self.chenh_den.date().toString("yyyy-MM-dd")
            sql = "SELECT cl.ngay, s.ten, cl.chenh, cl.ton_truoc, cl.ton_sau, cl.ghi_chu FROM ChenhLech cl JOIN SanPham s ON cl.sanpham_id = s.id WHERE date(cl.ngay) >= ? AND date(cl.ngay) <= ? ORDER BY cl.ngay DESC"
            c.execute(sql, (tu, den))
            rows = c.fetchall()
            self.tbl_chenhlech.setRowCount(len(rows))
            for i, r in enumerate(rows):
                for j, v in enumerate(r):
                    self.tbl_chenhlech.setItem(i, j, QTableWidgetItem(str(v)))
                # Thêm checkbox vào cột xử lý
                chk_item = QTableWidgetItem()
                chk_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                chk_item.setCheckState(Qt.Unchecked)
                self.tbl_chenhlech.setItem(i, 6, chk_item)
        except Exception as e:
            show_error(self, "Lỗi", f"Lỗi tải chênh lệch: {e}")
        finally:
            conn.close()

    def xu_ly_chenh_lech_click(self):
        # Lấy các dòng được chọn (checkbox checked)
        selected_rows = []
        for row in range(self.tbl_chenhlech.rowCount()):
            chk_item = self.tbl_chenhlech.item(row, 6)
            if chk_item and chk_item.checkState() == Qt.Checked:
                selected_rows.append(row)

        if not selected_rows:
            show_error(
                self, "Lỗi", "Vui lòng chọn ít nhất một dòng chênh lệch để xử lý"
            )
            return

        # Tạo dialog để chọn loại xử lý
        dialog = QDialog(self)
        dialog.setWindowTitle("Xử lý chênh lệch")
        layout = QVBoxLayout()

        xu_ly_label = QLabel("Chọn loại xử lý:")
        layout.addWidget(xu_ly_label)
        xu_ly_combo = QComboBox()
        xu_ly_combo.addItem("Bán bổ sung (nộp tiền)")
        xu_ly_combo.addItem("Trả lại tiền")
        xu_ly_combo.addItem("Thay thế hàng")
        xu_ly_combo.addItem("Coi như đã bán")
        layout.addWidget(xu_ly_combo)

        user_label = QLabel("Chọn user:")
        user_combo = QComboBox()
        from users import lay_tat_ca_user

        users = lay_tat_ca_user()
        for user in users:
            # Chấp nhận cả 'accountant' và 'Accountant'
            if str(user[2]).lower() == "accountant":  # user[2] là role
                user_combo.addItem(f"{user[1]} (ID: {user[0]})", user[0])
        layout.addWidget(user_label)
        layout.addWidget(user_combo)

        money_label = QLabel("Nhập số tiền:")
        money_edit = QLineEdit()
        money_edit.setValidator(QDoubleValidator())
        layout.addWidget(money_label)
        layout.addWidget(money_edit)

        # Ẩn/hiện user selector và money input dựa trên loại xử lý
        def on_xu_ly_changed(index):
            if index == 1:  # Trả lại tiền
                user_label.setVisible(True)
                user_combo.setVisible(True)
                money_label.setVisible(True)
                money_edit.setVisible(True)
            else:
                user_label.setVisible(False)
                user_combo.setVisible(False)
                money_label.setVisible(False)
                money_edit.setVisible(False)

        xu_ly_combo.currentIndexChanged.connect(on_xu_ly_changed)
        on_xu_ly_changed(0)  # Set initial visibility

        btn_ok = QPushButton("Xác nhận")
        btn_ok.clicked.connect(dialog.accept)
        layout.addWidget(btn_ok)

        dialog.setLayout(layout)

        if dialog.exec_() != QDialog.Accepted:
            return

        xu_ly_type = xu_ly_combo.currentIndex()

        # Xử lý từng dòng được chọn
        try:
            conn = ket_noi()
            c = conn.cursor()

            for row in selected_rows:
                ngay = self.tbl_chenhlech.item(row, 0).text()
                ten_sp = self.tbl_chenhlech.item(row, 1).text()
                chenh = float(self.tbl_chenhlech.item(row, 2).text())

                # Lấy thông tin sản phẩm
                from products import tim_sanpham

                sp = tim_sanpham(ten_sp)
                if not sp:
                    continue
                sp = sp[0]
                gia_le = sp[2]

                if xu_ly_type == 0:  # Bán bổ sung (nộp tiền)
                    # Cộng tiền vào số dư user
                    so_tien = abs(chenh) * gia_le
                    from users import chuyen_tien
                    from datetime import datetime

                    chuyen_tien(
                        self.user_id, self.user_id, so_tien, f"Bán bổ sung - {ten_sp}"
                    )

                elif xu_ly_type == 1:  # Trả lại tiền
                    # Trừ tiền từ accountant
                    accountant_id = user_combo.currentData()
                    so_tien_str = money_edit.text()
                    if not so_tien_str:
                        show_error(self, "Lỗi", "Vui lòng nhập số tiền")
                        continue
                    so_tien = float(so_tien_str)

                    # Trừ tiền từ accountant
                    c.execute(
                        "UPDATE Users SET so_du = so_du - ? WHERE id = ?",
                        (so_tien, accountant_id),
                    )
                    # Ghi log vào GiaoDichQuy
                    from datetime import datetime

                    c.execute(
                        "INSERT INTO GiaoDichQuy (user_id, user_nhan_id, so_tien, ngay, ghi_chu) VALUES (?, NULL, ?, ?, ?)",
                        (
                            accountant_id,
                            so_tien,
                            datetime.now().isoformat(),
                            f"Trả lại tiền - {ten_sp}",
                        ),
                    )

                elif xu_ly_type == 2:  # Thay thế hàng
                    # Không làm gì với tiền, chỉ ghi nhận
                    pass

                elif xu_ly_type == 3:  # Coi như đã bán
                    # Không làm gì
                    pass

                # Xóa dòng chênh lệch khỏi DB
                c.execute(
                    "DELETE FROM ChenhLech WHERE ngay = ? AND sanpham_id = (SELECT id FROM SanPham WHERE ten = ?)",
                    (ngay, ten_sp),
                )

            conn.commit()
            conn.close()

            show_success(
                self, f"Đã xử lý {len(selected_rows)} dòng chênh lệch"
            )
            # Reload bảng và xóa các dòng đã xử lý khỏi UI
            self.load_chenhlech()

        except Exception as e:
            show_error(self, "Lỗi", f"Lỗi xử lý chênh lệch: {e}")
            try:
                conn.close()
            except Exception as close_err:
                print(f"Warning: Could not close connection: {close_err}")

    def init_tab_banhang(self):
        layout = QVBoxLayout()

        # ✅ THÊM: Header với QDateTimeEdit để chọn thời gian ghi nhận hóa đơn
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("📅 Thời gian ghi nhận:"))
        
        self.datetime_hoadon = QDateTimeEdit()
        self.datetime_hoadon.setCalendarPopup(True)
        self.datetime_hoadon.setDisplayFormat("dd/MM/yyyy HH:mm:ss")
        self.datetime_hoadon.setDateTime(QDateTime.currentDateTime())
        
        header_layout.addWidget(self.datetime_hoadon)
        header_layout.addStretch()
        
        info_label = QLabel("💡 Tip: Có thể chỉnh sửa thời gian trước khi lưu hóa đơn")
        info_label.setStyleSheet("color: gray; font-style: italic;")
        header_layout.addWidget(info_label)
        
        layout.addLayout(header_layout)

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

        # Nút thêm dòng và Lưu - xếp ngang góc phải
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_them_dong = QPushButton("Thêm dòng")
        btn_them_dong.clicked.connect(self.them_dong_giohang)
        btn_layout.addWidget(btn_them_dong)
        # Rename button to 'Lưu' to avoid confusion. Start disabled until nhận hàng xong.
        self.btn_luu = QPushButton("Lưu")
        self.btn_luu.setEnabled(False)
        self.btn_luu.clicked.connect(self.tao_hoa_don_click)
        btn_layout.addWidget(self.btn_luu)

        # Button to close shift (preview and print) - placed in Bán hàng so it's accessible when Nhận hàng is locked
        btn_close_shift = QPushButton("Đóng ca (In tổng kết)")
        btn_close_shift.clicked.connect(self.dong_ca_in_pdf)
        btn_layout.addWidget(btn_close_shift)

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
        setup_quantity_spinbox(sl_spin, decimals=5, maximum=9999)
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
                    don_gia = chon_don_gia(sp, sl, is_vip)
                    print(f"Selected don_gia: {don_gia}")  # Debug
                    self.tbl_giohang.setItem(
                        row, 2, QTableWidgetItem(format_price(don_gia))
                    )
                except (ValueError, TypeError):
                    print(f"Invalid price data for product '{ten}'")  # Debug
                    # Reconnect signal trước khi return
                    self.tbl_giohang.itemChanged.connect(self.update_giohang)
                    return  # Không làm gì nếu dữ liệu giá không hợp lệ
            else:
                # Product not found in DB
                print(f"Sản phẩm '{ten}' không tồn tại")  # Debug
                show_error(self, "Lỗi", f"Sản phẩm '{ten}' không tồn tại")
                self.tbl_giohang.setItem(row, 2, QTableWidgetItem(format_price(0)))
                don_gia = 0
                # Clear name to avoid creating invalid invoice
                self.tbl_giohang.setItem(row, 0, QTableWidgetItem(""))
                self.tbl_giohang.itemChanged.connect(self.update_giohang)
                return

        # Check availability: product must have been received
        if ten:
            avail_qty = self.available_products.get(ten, 0)
            if avail_qty <= 0:
                show_error(
                    self,
                    "Lỗi",
                    f"Sản phẩm '{ten}' chưa được nhận hàng nên không thể bán",
                )
                # reset name and price
                self.tbl_giohang.setItem(row, 0, QTableWidgetItem(""))
                self.tbl_giohang.setItem(row, 2, QTableWidgetItem(format_price(0)))
                self.tbl_giohang.itemChanged.connect(self.update_giohang)
                return

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
                show_error(self, "Lỗi", f"Dòng {row+1} thiếu dữ liệu")
                return

            ten = ten_item.text().strip()
            res = tim_sanpham(ten)
            if not res:
                show_error(self, "Lỗi", f"Sản phẩm '{ten}' không tồn tại")
                return
            sanpham_id = res[0][0]
            so_luong = sl_spin.value() if sl_spin else 0
            try:
                gia = float(don_gia_item.text().replace(",", ""))
            except (ValueError, TypeError):
                show_error(self, "Lỗi", f"Giá không hợp lệ ở dòng {row+1}")
                return
            giam = giam_spin.value() if giam_spin else 0
            loai_gia = xac_dinh_loai_gia(
                so_luong,
                res[0][6] if len(res[0]) > 6 else 0,
                vip_item.checkState() == Qt.Checked,
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
            show_error(self, "Lỗi", "Giỏ hàng rỗng")
            return

        # ✅ Lấy thời gian từ QDateTimeEdit
        ngay_ghi_nhan = self.datetime_hoadon.dateTime().toString("yyyy-MM-dd HH:mm:ss")

        print(f"Items before tao_hoa_don: {items}")
        print(f"Ngày ghi nhận: {ngay_ghi_nhan}")
        try:
            khach_hang = ""
            uu_dai = 0
            xuat_hoa_don = 0
            giam_gia = 0
            success, msg, _ = tao_hoa_don(
                self.user_id, khach_hang, items, uu_dai, xuat_hoa_don, giam_gia, ngay_ghi_nhan
            )
        except Exception as e:
            print(f"Error calling tao_hoa_don: {str(e)}")
            show_error(self, "Lỗi", f"Lỗi gọi tao_hoa_don: {str(e)}")
            return

        if not success:
            print(f"tao_hoa_don failed: {msg}")
            show_error(self, "Lỗi", msg)
            return

        # Deduct sold quantities from available_products
        for it in items:
            try:
                # find product name by id
                from products import tim_sanpham_by_id

                # fallback: try lookup by id via DB select
                # We will attempt to get name from DB via tim_sanpham (which accepts name),
                # so instead query all and match id.
                conn = ket_noi()
                c = conn.cursor()
                c.execute("SELECT ten FROM SanPham WHERE id=?", (it["sanpham_id"],))
                row = c.fetchone()
                if row:
                    name = row[0]
                else:
                    name = None
            except Exception:
                name = None

            if name:
                prev = self.available_products.get(name, 0)
                new = prev - it["so_luong"]
                if new < 0:
                    new = 0
                self.available_products[name] = new

        # refresh completers after sale
        self.cap_nhat_completer_sanpham()

        show_success(
            self, f"Tạo hóa đơn thành công, ID: {msg}"
        )
        
        # Tự động làm mới các tab liên quan
        self.load_chitietban()  # Tab chi tiết bán
        self.load_hoadon()  # Tab hóa đơn
        self.load_so_quy()  # Tab sổ quỹ

        # ✅ Reset thời gian về hiện tại sau khi lưu thành công
        self.datetime_hoadon.setDateTime(QDateTime.currentDateTime())

        # Lưu lại ID hóa đơn mới nhất
        try:
            self.last_invoice_id = int(msg)
        except Exception as e:
            print(f"Warning: Could not parse invoice ID '{msg}': {e}")
            self.last_invoice_id = None

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

        # Nút hành động
        btn_layout = QHBoxLayout()
        btn_refresh = QPushButton("Làm mới")
        btn_refresh.clicked.connect(self.load_chitietban)
        btn_layout.addWidget(btn_refresh)
        
        # Chỉ admin mới có quyền sửa/xóa hóa đơn trong tab này
        if self.role == "admin":
            btn_sua_hd_chitiet = QPushButton("✏️ Sửa hóa đơn")
            btn_sua_hd_chitiet.clicked.connect(self.sua_hoadon_chitiet_admin)
            btn_layout.addWidget(btn_sua_hd_chitiet)
            
            btn_xoa_hd_chitiet = QPushButton("🗑️ Xóa hóa đơn")
            btn_xoa_hd_chitiet.clicked.connect(self.xoa_hoadon_chitiet_admin)
            btn_layout.addWidget(btn_xoa_hd_chitiet)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

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
            unpaid_total = tinh_unpaid_total(chi_tiet)

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

            # Thay nút "Chi tiết" bằng text link màu xanh
            link_detail = QLabel(
                f'<a href="#" style="color: #0A6CBF; text-decoration: none; font-weight: bold;">Chi tiết</a>'
            )
            link_detail.setAlignment(Qt.AlignCenter)
            link_detail.setOpenExternalLinks(False)
            link_detail.linkActivated.connect(lambda _, r=row_idx: self.xem_chi_tiet(r))
            link_detail.setCursor(Qt.PointingHandCursor)
            self.tbl_chitietban.setCellWidget(row_idx, 6, link_detail)

            # Tất cả user đều thấy nút "Nộp tiền"
            btn_nop = QPushButton("Nộp tiền")
            btn_nop.clicked.connect(lambda checked, r=row_idx: self.nop_tien(r))
            # giữ mặc định hệ thống
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
            # Tính chênh lệch dùng helper, lấy gia_buon khi cần
            try:
                lg = row[5]
                xhd = row[7]
                sl = row[4]
                gia_le = row[8]
                giam = row[9]
            except Exception:
                lg = None
                xhd = 0
                sl = 0
                gia_le = 0
                giam = 0

            gia_buon_val = None
            if str(lg).lower() == "le":
                from products import tim_sanpham

                sp_info = tim_sanpham(row[3])  # row[3] là tên sản phẩm
                if sp_info:
                    gia_buon_val = sp_info[0][3]
            chenh = tinh_chenh_lech(lg, xhd, sl, gia_le, giam, gia_buon_val)
            # Debug log giữ nguyên thông tin hữu ích
            try:
                print(
                    f"DEBUG DA XUAT - SP: {row[3]}, gia_le: {gia_le}, gia_buon: {gia_buon_val if gia_buon_val is not None else 'N/A'}, sl: {sl}, giam: {giam}, chenh: {chenh}"
                )
            except Exception:
                pass
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
            # Tính chênh lệch dùng helper, lấy gia_buon khi cần
            try:
                lg = row[5]
                xhd = row[7]
                sl = row[4]
                gia_le = row[8]
                giam = row[9]
            except Exception:
                lg = None
                xhd = 0
                sl = 0
                gia_le = 0
                giam = 0

            gia_buon_val = None
            if str(lg).lower() == "le":
                from products import tim_sanpham

                sp_info = tim_sanpham(row[3])  # row[3] là tên sản phẩm
                if sp_info:
                    gia_buon_val = sp_info[0][3]
            chenh = tinh_chenh_lech(lg, xhd, sl, gia_le, giam, gia_buon_val)
            # Debug log giữ nguyên thông tin hữu ích
            try:
                print(
                    f"DEBUG CHUA XUAT - SP: {row[3]}, gia_le: {gia_le}, gia_buon: {gia_buon_val if gia_buon_val is not None else 'N/A'}, sl: {sl}, giam: {giam}, chenh: {chenh}"
                )
            except Exception:
                pass
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

        # Tính số dư hiện tại từ DB: unpaid_total - paid
        from users import lay_tong_nop_theo_hoadon

        chi_tiet = lay_chi_tiet_hoadon(hoadon_id)
        unpaid_total = tinh_unpaid_total(chi_tiet)
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
            show_error(self, "Lỗi", "Không tìm thấy user accountant")
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
        self,
        user_id_from,
        accountant_id,
        so_tien_str,
        so_du_hien_tai,
        dialog,
        row,
        hoadon_id=None,
    ):
        """Xác nhận nộp tiền"""
        try:
            so_tien = float(so_tien_str.replace(",", ""))
            if so_tien <= 0:
                show_error(self, "Lỗi", "Số tiền phải lớn hơn 0")
                return
            if so_tien > so_du_hien_tai:
                show_error(
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
                    show_success(
                        self,
                        f"Nộp tiền thành công! Số dư về 0. Sản phẩm vẫn ở trạng thái chưa xuất hóa đơn.",
                    )
                else:
                    show_success(
                        self,
                        f"Nộp tiền thành công! Số dư còn lại: {format_price(so_du_con_lai)}. Sản phẩm vẫn ở trạng thái chưa xuất hóa đơn.",
                    )
                self.load_chitietban()  # Làm mới bảng
                self.load_so_quy()  # Tự động làm mới tab Sổ quỹ
                self.load_lich_su_quy()  # Tự động làm mới lịch sử giao dịch
                dialog.close()
            else:
                show_error(self, "Lỗi", f"Chuyển tiền thất bại: {msg}")
        except ValueError:
            show_error(self, "Lỗi", "Số tiền không hợp lệ")

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
        self.to_tien_spins_phieu_thu = []
        for mg in MENH_GIA:
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
            show_success(self, "In phiếu thu thành công!")
            dialog.close()

    def sua_hoadon_chitiet_admin(self):
        """Chỉ admin mới được sửa hóa đơn trong tab Chi tiết bán"""
        row = self.tbl_chitietban.currentRow()
        if row < 0:
            show_warning(self, "Vui lòng chọn hóa đơn cần sửa")
            return
        
        hoadon_id = int(self.tbl_chitietban.item(row, 0).text())
        ngay_cu = self.tbl_chitietban.item(row, 3).text()
        
        # Dialog nhập thông tin mới
        from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Sửa hóa đơn #{hoadon_id}")
        form = QFormLayout()
        
        # QDateTimeEdit cho ngày giờ
        from PyQt5.QtCore import QDateTime
        txt_ngay = QDateTimeEdit()
        txt_ngay.setDisplayFormat("dd/MM/yyyy HH:mm:ss")
        txt_ngay.setCalendarPopup(True)
        # Parse ngày cũ
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
            
            from invoices import sua_hoa_don
            if sua_hoa_don(hoadon_id, ngay=ngay_moi, ghi_chu=ghi_chu):
                show_success(self, "Đã sửa hóa đơn")
                self.load_chitietban()
            else:
                show_error(self, "Lỗi khi sửa hóa đơn")

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
            "⚠️ Thao tác này không thể hoàn tác!"
        ):
            return
        
        from invoices import xoa_hoa_don
        if xoa_hoa_don(hoadon_id):
            show_success(self, "Đã xóa hóa đơn")
            self.load_chitietban()
        else:
            show_error(self, "Lỗi khi xóa hóa đơn")

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
        except Exception as e:
            show_error(self, "Lỗi", f"Hóa đơn ID không hợp lệ: {e}")

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
        # Thêm cột ID để admin có thể sửa/xóa
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
        self.setup_table(self.tbl_hoadon)
        layout.addWidget(self.tbl_hoadon)

        # Label tổng tiền
        self.lbl_tong_hoadon = QLabel("Tổng XHĐ: 0")
        layout.addWidget(self.lbl_tong_hoadon)

        # Nút hành động
        btn_layout = QHBoxLayout()
        btn_export = QPushButton("Export Excel")
        btn_export.clicked.connect(self.export_hoadon_excel)
        btn_layout.addWidget(btn_export)
        
        # Chỉ admin mới có quyền sửa/xóa
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

            # Admin cần thêm ID để sửa/xóa
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
                if self.role == "admin":
                    hoadon_id, chitiet_id, ngay, username, ten_sp, so_luong, loai_gia, tong_tien_item = row
                    
                    # Chuyển đổi loại giá
                    loai_gia_text = {"le": "Lẻ", "buon": "Buôn", "vip": "VIP"}.get(
                        loai_gia, loai_gia
                    )

                    self.tbl_hoadon.setItem(row_idx, 0, QTableWidgetItem(str(hoadon_id)))
                    self.tbl_hoadon.setItem(row_idx, 1, QTableWidgetItem(str(chitiet_id)))
                    self.tbl_hoadon.setItem(row_idx, 2, QTableWidgetItem(ngay))
                    self.tbl_hoadon.setItem(row_idx, 3, QTableWidgetItem(username))
                    self.tbl_hoadon.setItem(row_idx, 4, QTableWidgetItem(ten_sp))
                    self.tbl_hoadon.setItem(row_idx, 5, QTableWidgetItem(str(so_luong)))
                    self.tbl_hoadon.setItem(row_idx, 6, QTableWidgetItem(loai_gia_text))
                    self.tbl_hoadon.setItem(
                        row_idx, 7, QTableWidgetItem(format_price(tong_tien_item))
                    )
                else:
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
                show_success(self, "Export thành công")

    def sua_chi_tiet_hoadon_admin(self):
        """Chỉ admin mới được sửa chi tiết hóa đơn"""
        row = self.tbl_hoadon.currentRow()
        if row < 0:
            show_warning(self, "Vui lòng chọn chi tiết hóa đơn cần sửa")
            return
        
        chitiet_id = int(self.tbl_hoadon.item(row, 1).text())
        ten_sp = self.tbl_hoadon.item(row, 4).text()
        so_luong_cu = self.tbl_hoadon.item(row, 5).text()
        
        # Dialog nhập thông tin mới
        from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox
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
                
                from invoices import sua_chi_tiet_hoa_don
                if sua_chi_tiet_hoa_don(chitiet_id, so_luong=so_luong_moi, ghi_chu=ghi_chu):
                    show_success(self, "Đã sửa chi tiết hóa đơn")
                    self.load_hoadon()
                else:
                    show_error(self, "Lỗi khi sửa chi tiết hóa đơn")
            except ValueError:
                show_error(self, "Số lượng không hợp lệ")

    def xoa_chi_tiet_hoadon_admin(self):
        """Chỉ admin mới được xóa chi tiết hóa đơn"""
        row = self.tbl_hoadon.currentRow()
        if row < 0:
            show_warning(self, "Vui lòng chọn chi tiết hóa đơn cần xóa")
            return
        
        chitiet_id = int(self.tbl_hoadon.item(row, 1).text())
        ten_sp = self.tbl_hoadon.item(row, 4).text()
        
        if not show_confirmation(
            self, 
            f"Bạn có chắc chắn muốn xóa chi tiết:\n{ten_sp}?\n\n⚠️ Thao tác này không thể hoàn tác!"
        ):
            return
        
        from invoices import xoa_chi_tiet_hoa_don
        if xoa_chi_tiet_hoa_don(chitiet_id):
            show_success(self, "Đã xóa chi tiết hóa đơn")
            self.load_hoadon()
        else:
            show_error(self, "Lỗi khi xóa chi tiết hóa đơn")

    def sua_hoadon_admin(self):
        """Chỉ admin mới được sửa thông tin hóa đơn"""
        row = self.tbl_hoadon.currentRow()
        if row < 0:
            show_warning(self, "Vui lòng chọn hóa đơn cần sửa")
            return
        
        hoadon_id = int(self.tbl_hoadon.item(row, 0).text())
        ngay_cu = self.tbl_hoadon.item(row, 2).text()
        
        # Dialog nhập thông tin mới
        from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Sửa hóa đơn #{hoadon_id}")
        form = QFormLayout()
        
        # QDateTimeEdit cho ngày giờ
        from PyQt5.QtCore import QDateTime
        txt_ngay = QDateTimeEdit()
        txt_ngay.setDisplayFormat("dd/MM/yyyy HH:mm:ss")
        txt_ngay.setCalendarPopup(True)
        # Parse ngày cũ
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
            
            from invoices import sua_hoa_don
            if sua_hoa_don(hoadon_id, ngay=ngay_moi, ghi_chu=ghi_chu):
                show_success(self, "Đã sửa hóa đơn")
                self.load_hoadon()
            else:
                show_error(self, "Lỗi khi sửa hóa đơn")

    def xoa_hoadon_admin(self):
        """Chỉ admin mới được xóa hóa đơn"""
        row = self.tbl_hoadon.currentRow()
        if row < 0:
            show_warning(self, "Vui lòng chọn hóa đơn cần xóa")
            return
        
        hoadon_id = int(self.tbl_hoadon.item(row, 0).text())
        
        if not show_confirmation(
            self, 
            f"Bạn có chắc chắn muốn xóa hóa đơn #{hoadon_id}?\n\n"
            "⚠️ Tất cả chi tiết hóa đơn liên quan sẽ bị xóa!\n"
            "⚠️ Thao tác này không thể hoàn tác!"
        ):
            return
        
        from invoices import xoa_hoa_don
        if xoa_hoa_don(hoadon_id):
            show_success(self, "Đã xóa hóa đơn")
            self.load_hoadon()
        else:
            show_error(self, "Lỗi khi xóa hóa đơn")

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
        # Columns order: Tên, Tồn kho, Số lượng XHĐ, Số lượng xuất bổ, Số lượng chưa xuất, SYS, Trạng thái
        self.tbl_baocao_kho.setColumnCount(7)
        self.tbl_baocao_kho.setHorizontalHeaderLabels(
            [
                "Tên sản phẩm",
                "Tồn kho",
                "Số lượng XHĐ",
                "Số lượng xuất bổ",
                "Số lượng chưa xuất",
                "SYS",
                "Trạng thái",
            ]
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
        self.bieudo_year.addItems(
            [str(year) for year in range(current_year - 5, current_year + 1)]
        )
        self.bieudo_year.setCurrentText(str(current_year))
        filter_layout.addWidget(self.bieudo_year)

        # Lọc theo tháng
        filter_layout.addWidget(QLabel("Tháng:"))
        self.bieudo_month = QComboBox()
        self.bieudo_month.addItems(["Tất cả"] + [str(m) for m in range(1, 13)])
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
            c.execute(
                "SELECT id, ten, ton_kho, gia_buon, nguong_buon FROM SanPham ORDER BY ten"
            )
            san_pham_list = c.fetchall()

            # Sắp xếp theo thứ tự tùy chỉnh (các tên không có trong danh sách sẽ đứng sau, theo ABC)
            custom_order = [
                "PLC KOMAT SUPER 20W/40 200 lít",
                "PLC KOMAT SUPER 20W/50 200 lít",
                "PLC RACER PLUS 4 lít",
                "PLC RACER 2T 1 lít",
                "PLC RACER SF 0.8 lít",
                "PLC RACER SF 1 lít",
                "PLC RACER SJ 1 lít",
                "PLC RACER SCOOTER 0.8 lít",
                "PLC KOMAT SHD/40 18 lít",
                "PLC KOMAT SHD 40 4 lít",
                "PLC KOMAT SHD/50 18 lít",
                "PLC KOMAT SHD/50 25 lít",
                "PLC CACER CI-4 15W/40 5 lít",
                "PLC CARTER CI-4 15W/40 18 lít",
                "PLC KOMAT SHD/40 25 lít",
                "PCL GEAR OIL MP 90EP 4 lít",
                "PLC GEAR OIL MP 140EP 4 lít",
                "PLC-AW HYDROIL 68 209 lít",
                "PLC-AW HYDROIL 68 18 lít",
            ]
            order_map = {name: idx for idx, name in enumerate(custom_order)}

            def _sort_key(sp_row):
                ten_sp = sp_row[1] or ""
                return (order_map.get(ten_sp, 10_000), ten_sp)

            try:
                san_pham_list.sort(key=_sort_key)
            except Exception:
                pass

            # Chuẩn bị data cho bảng
            table_data = []
            for sp in san_pham_list:
                sp_id, ten, ton_kho, _, nguong_buon = sp

                # Lấy số lượng đã xuất hóa đơn
                c.execute(
                    """
                    SELECT COALESCE(SUM(so_luong), 0)
                    FROM ChiTietHoaDon 
                    WHERE sanpham_id = ? AND xuat_hoa_don = 1
                """,
                    (sp_id,),
                )
                sl_xhd = c.fetchone()[0] or 0

                # Lấy số lượng đã xuất bổ (chuẩn hóa theo 'xuatbo' mới, vẫn hỗ trợ dữ liệu cũ)
                try:
                    c.execute(
                        """
                        SELECT COALESCE(SUM(so_luong), 0)
                        FROM LogKho 
                        WHERE sanpham_id = ? AND hanh_dong IN ('xuatbo','xuat_bo')
                    """,
                        (sp_id,),
                    )
                    sl_xuat_bo = c.fetchone()[0] or 0
                except Exception:
                    # Fallback: một số DB cũ có thể dùng 'xuat'
                    c.execute(
                        """
                        SELECT COALESCE(SUM(so_luong), 0)
                        FROM LogKho 
                        WHERE sanpham_id = ? AND hanh_dong = 'xuat'
                    """,
                        (sp_id,),
                    )
                    sl_xuat_bo = c.fetchone()[0] or 0

                # Lấy số lượng chưa xuất
                # Gồm: (1) số lượng bán chưa xuất từ ChiTietHoaDon (xuat_hoa_don=0)
                #      (2) số lượng đầu kỳ (DauKyXuatBo) còn lại
                try:
                    c.execute(
                        """
                        SELECT COALESCE(SUM(so_luong), 0)
                        FROM ChiTietHoaDon 
                        WHERE sanpham_id = ? AND xuat_hoa_don = 0
                        """,
                        (sp_id,),
                    )
                    sl_chua_xuat_cthd = c.fetchone()[0] or 0
                except Exception:
                    sl_chua_xuat_cthd = 0

                # DauKyXuatBo: dùng sanpham_id để cộng dồn số lượng đầu kỳ còn tồn
                try:
                    c.execute(
                        """
                        SELECT COALESCE(SUM(so_luong), 0)
                        FROM DauKyXuatBo
                        WHERE sanpham_id = ?
                        """,
                        (sp_id,),
                    )
                    sl_dau_ky = c.fetchone()[0] or 0
                except Exception:
                    sl_dau_ky = 0

                sl_chua_xuat = (sl_chua_xuat_cthd or 0) + (sl_dau_ky or 0)

                # SYS = tồn kho hiện tại + số lượng chưa xuất hóa đơn
                # (theo yêu cầu: SYS = kho + số lượng chưa xuất hóa đơn)
                try:
                    sys_val = (ton_kho or 0) + (sl_chua_xuat or 0)
                except Exception:
                    sys_val = 0

                # Kiểm tra trạng thái tồn kho vs ngưỡng buôn
                trang_thai = ""
                if ton_kho is None:
                    ton_kho = 0
                if nguong_buon is None:
                    nguong_buon = 0
                if ton_kho < nguong_buon:
                    trang_thai = "Dưới ngưỡng buôn"

                # Build row in the chosen column order (see header)
                table_data.append(
                    [
                        ten,
                        ton_kho,
                        sl_xhd,
                        sl_xuat_bo,
                        sl_chua_xuat,
                        sys_val,
                        trang_thai,
                    ]
                )

                # Debug print to console so you can verify values easily
                try:
                    print(
                        f"BAOCAOKHO: {ten} | ton_kho={ton_kho} | sl_xhd={sl_xhd} | sl_xuat_bo={sl_xuat_bo} | sl_chua_xuat(cthd+dk)={sl_chua_xuat} | SYS={sys_val}"
                    )
                except Exception:
                    pass

            # Hiển thị dữ liệu (đã sắp xếp theo thứ tự tùy chỉnh ở trên)
            self.tbl_baocao_kho.setRowCount(len(table_data))
            for row_idx, row_data in enumerate(table_data):
                for col_idx, val in enumerate(row_data):
                    # Format numeric values for readability
                    if col_idx in [1, 2, 3, 4, 5]:
                        # these are numeric: Tồn kho, Số lượng XHĐ, Số lượng xuất bổ, Số lượng chưa xuất, SYS
                        try:
                            txt = format_price(float(val))
                        except Exception:
                            txt = str(val)
                        item = QTableWidgetItem(txt)
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    else:
                        item = QTableWidgetItem(str(val))

                    # Highlight important columns: Số lượng chưa xuất (index 4) and SYS (index 5)
                    try:
                        if col_idx == 4 and float(row_data[4]) > 0:
                            item.setBackground(Qt.yellow)
                        if col_idx == 5:
                            item.setBackground(Qt.lightGray)
                    except Exception:
                        pass

                    # Trang thái nằm ở cột cuối (index 6)
                    if col_idx == 6 and row_data[6]:
                        # If there's a warning string, also color it
                        item.setBackground(Qt.yellow)

                    self.tbl_baocao_kho.setItem(row_idx, col_idx, item)

        except Exception as e:
            show_error(self, "Lỗi", f"Lỗi truy vấn dữ liệu: {str(e)}")
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
                ax.bar([xi + i * width for xi in x], qty, width, label=product)

            ax.set_xticks([xi + (len(products) - 1) * width / 2 for xi in x])
            ax.set_xticklabels([f"Tháng {m}" for m in months])

            ax.set_ylabel("Sản lượng")
            ax.set_title(
                f"Sản lượng theo sản phẩm năm {nam}"
                + (f" - Tháng {thang}" if thang != "Tất cả" else "")
            )

            if len(products) > 1:
                ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")

            self.figure.tight_layout()
            self.canvas.draw()

        except Exception as e:
            show_error(self, "Lỗi", f"Lỗi vẽ biểu đồ: {str(e)}")
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
        btn_layout.addStretch()
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
                show_success(self, "Thêm user thành công")
                self.load_users()
            else:
                show_error(self, "Lỗi", "Thêm user thất bại")

    def xoa_user_click(self):
        row = self.tbl_user.currentRow()
        if row < 0:
            show_error(self, "Lỗi", "Chọn một user")
            return
        user_id = int(self.tbl_user.item(row, 0).text())
        if user_id == self.user_id:
            show_error(self, "Lỗi", "Không thể xóa chính mình")
            return
        if xoa_user(user_id):
            show_success(self, "Xóa user thành công")
            self.load_users()
        else:
            show_error(self, "Lỗi", "Xóa user thất bại")

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

        # === HÀNG 1: 3 BẢNG CHƯA XUẤT ===
        chua_xuat_layout = QHBoxLayout()

        # Bảng 1: Chưa xuất - Giá Buôn
        buon_layout = QVBoxLayout()
        lbl_buon_chua = QLabel("CHƯA XUẤT - GIÁ BUÔN")
        buon_layout.addWidget(lbl_buon_chua)
        self.tbl_xuatbo_buon = QTableWidget()
        self.tbl_xuatbo_buon.setColumnCount(2)
        self.tbl_xuatbo_buon.setHorizontalHeaderLabels(["Tên sản phẩm", "Số lượng"])
        self.setup_table(self.tbl_xuatbo_buon)
        buon_layout.addWidget(self.tbl_xuatbo_buon)
        chua_xuat_layout.addLayout(buon_layout)

        # Bảng 2: Chưa xuất - Giá VIP
        vip_layout = QVBoxLayout()
        lbl_vip_chua = QLabel("CHƯA XUẤT - GIÁ VIP")
        vip_layout.addWidget(lbl_vip_chua)
        self.tbl_xuatbo_vip = QTableWidget()
        self.tbl_xuatbo_vip.setColumnCount(2)
        self.tbl_xuatbo_vip.setHorizontalHeaderLabels(["Tên sản phẩm", "Số lượng"])
        self.setup_table(self.tbl_xuatbo_vip)
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
        self.setup_table(self.tbl_xuatbo_le)
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
        self.setup_table(self.tbl_xuatdu_buon)
        buon_du_layout.addWidget(self.tbl_xuatdu_buon)
        xuat_du_layout.addLayout(buon_du_layout)

        # Bảng 5: Xuất dư - Giá VIP
        vip_du_layout = QVBoxLayout()
        lbl_vip_du = QLabel("XUẤT DƯ - GIÁ VIP")
        vip_du_layout.addWidget(lbl_vip_du)
        self.tbl_xuatdu_vip = QTableWidget()
        self.tbl_xuatdu_vip.setColumnCount(2)
        self.tbl_xuatdu_vip.setHorizontalHeaderLabels(["Tên sản phẩm", "Số lượng"])
        self.setup_table(self.tbl_xuatdu_vip)
        vip_du_layout.addWidget(self.tbl_xuatdu_vip)
        xuat_du_layout.addLayout(vip_du_layout)

        # Bảng 6: Xuất dư - Giá Lẻ
        le_du_layout = QVBoxLayout()
        lbl_le_du = QLabel("XUẤT DƯ - GIÁ LẺ")
        le_du_layout.addWidget(lbl_le_du)
        self.tbl_xuatdu_le = QTableWidget()
        self.tbl_xuatdu_le.setColumnCount(2)
        self.tbl_xuatdu_le.setHorizontalHeaderLabels(["Tên sản phẩm", "Số lượng"])
        self.setup_table(self.tbl_xuatdu_le)
        le_du_layout.addWidget(self.tbl_xuatdu_le)
        xuat_du_layout.addLayout(le_du_layout)

        layout.addLayout(xuat_du_layout)

        # Footer: Form nhập xuất bổ - MỞ RỘNG
        lbl_xuat_bo_manual = QLabel("--- XUẤT BỔ THỦ CÔNG ---")
        layout.addWidget(lbl_xuat_bo_manual)
        footer_layout = QVBoxLayout()

        # Danh sách các dòng nhập
        self.xuat_bo_rows = []
        self.xuat_bo_table = QTableWidget()
        self.xuat_bo_table.setColumnCount(4)
        self.xuat_bo_table.setHorizontalHeaderLabels(
            ["Tên sản phẩm", "Số lượng", "Loại giá", "Tiền"]
        )
        self.setup_table(self.xuat_bo_table)
        # Tăng chiều cao hàng để ô nhập dễ thao tác
        self.xuat_bo_table.verticalHeader().setDefaultSectionSize(48)
        # Tăng độ rộng cột Tên sản phẩm để hiển thị đầy đủ - MỞ RỘNG HƠN
        self.xuat_bo_table.setColumnWidth(0, 400)  # Tăng từ 300 lên 400px
        self.xuat_bo_table.setColumnWidth(1, 120)  # Số lượng
        self.xuat_bo_table.setColumnWidth(2, 120)  # Loại giá
        # Đặt height tối thiểu cho bảng để hiện nhiều dòng hơn
        self.xuat_bo_table.setMinimumHeight(350)
        footer_layout.addWidget(self.xuat_bo_table)

        # Hàng chứa Label tổng + 3 nút (Làm mới, Thêm dòng, Xuất bổ)
        bottom_row = QHBoxLayout()

        # Label tổng tiền
        self.lbl_tong_xuat_bo = QLabel("Tổng: 0")
        bottom_row.addWidget(self.lbl_tong_xuat_bo)

        bottom_row.addStretch()

        # Nút làm mới
        btn_refresh = QPushButton("Làm mới")
        btn_refresh.clicked.connect(self.load_xuatbo)
        bottom_row.addWidget(btn_refresh)

        # Nút thêm dòng (kích thước vừa)
        btn_them_dong = QPushButton("Thêm dòng")
        btn_them_dong.clicked.connect(self.them_dong_xuat_bo)
        bottom_row.addWidget(btn_them_dong)

        # Nút xuất bổ (kích thước vừa, nổi bật hơn)
        btn_xuat_bo = QPushButton("XUẤT BỔ")
        btn_xuat_bo.clicked.connect(self.xuat_bo_click)
        bottom_row.addWidget(btn_xuat_bo)

        footer_layout.addLayout(bottom_row)

        layout.addLayout(footer_layout)

        self.load_xuatbo()
        # Thêm 5 dòng rỗng ban đầu
        for _ in range(5):
            self.them_dong_xuat_bo()

        self.tab_xuat_bo.setLayout(layout)

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
        from db import ket_noi

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
        from products import tim_sanpham

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
        ten_edit.setCompleter(self.tao_completer_sanpham())
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
        Logic xuất bổ mới:
        - XUẤT LẺ: chỉ lấy từ "Chưa xuất Lẻ" → thiếu → hỏi xuất dư
        - XUẤT BUÔN: kiểm tra ngưỡng → lấy "Chưa xuất Buôn" → thiếu lấy "Chưa xuất Lẻ" → vẫn thiếu → hỏi xuất dư
        - XUẤT VIP: lấy "Chưa xuất VIP" → thiếu lấy "Chưa xuất Buôn" → thiếu lấy "Chưa xuất Lẻ" → vẫn thiếu → hỏi xuất dư
        
        CHÊNH LỆCH: Tính SAU KHI XUẤT BỔ = (Giá đã bán - Giá xuất bổ)
        """
        from products import tim_sanpham
        from db import ket_noi
        
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
            
            items.append({
                "ten": ten,
                "so_luong": sl_yeu_cau,
                "loai_gia": loai_gia
            })
        
        if not items:
            show_error(self, "Lỗi", "Không có sản phẩm để xuất")
            return
        
        # 2. Xử lý từng sản phẩm
        xuat_du_list = []  # [(ten, sl_du, loai_gia)]
        xuat_plan = []  # Chi tiết kế hoạch xuất
        
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
            
            # Lấy số lượng hiện có
            sl_chua_xuat_le = self.get_sl_from_table("le", ten)
            sl_chua_xuat_buon = self.get_sl_from_table("buon", ten)
            sl_chua_xuat_vip = self.get_sl_from_table("vip", ten)
            
            # === XỬ LÝ THEO LOẠI GIÁ ===
            plan = {
                "ten": ten,
                "loai_gia_xuat": loai_gia,
                "sl_yeu_cau": sl_yeu_cau,
                "chi_tiet": []  # [(loai_gia_nguon, so_luong)]
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
                        QMessageBox.Yes | QMessageBox.No
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
                        f"{ten}: Xuất giá buôn phải >= {nguong_buon}\n(Đang yêu cầu: {sl_yeu_cau})"
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
                        f"{ten} - Giá buôn thiếu {sl_con_thieu}\nLấy từ bảng chưa xuất giá lẻ?\n(Có: {sl_chua_xuat_le})\n\n→ Sẽ tính chênh lệch sau khi xuất bổ",
                        QMessageBox.Yes | QMessageBox.No
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
                        QMessageBox.Yes | QMessageBox.No
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
                        f"{ten} - Giá VIP thiếu {sl_con_thieu}\nLấy từ bảng chưa xuất giá buôn?\n(Có: {sl_chua_xuat_buon})\n\n→ Sẽ tính chênh lệch sau khi xuất bổ",
                        QMessageBox.Yes | QMessageBox.No
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
                        f"{ten} - Giá VIP vẫn thiếu {sl_con_thieu}\nLấy từ bảng chưa xuất giá lẻ?\n(Có: {sl_chua_xuat_le})\n\n→ Sẽ tính chênh lệch sau khi xuất bổ",
                        QMessageBox.Yes | QMessageBox.No
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
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply != QMessageBox.Yes:
                        return
                    
                    xuat_du_list.append((ten, sl_con_thieu, "vip"))
            
            xuat_plan.append(plan)
        
        # 3. Thực hiện xuất bổ và tính chênh lệch
        conn = ket_noi()
        c = conn.cursor()
        
        tong_chenh_lech = 0
        chenh_lech_chi_tiet = []  # Để hiển thị sau
        
        try:
            for plan in xuat_plan:
                ten = plan["ten"]
                loai_gia_xuat = plan["loai_gia_xuat"]
                
                # Lấy giá xuất bổ (giá catalog hiện tại)
                sp_info = tim_sanpham(ten)
                if not sp_info:
                    continue
                sp = sp_info[0]
                gia_le_catalog = float(sp[2])
                gia_buon_catalog = float(sp[3])
                gia_vip_catalog = float(sp[4])
                
                # Xác định giá xuất bổ
                if loai_gia_xuat == "vip":
                    gia_xuat_bo = gia_vip_catalog
                elif loai_gia_xuat == "buon":
                    gia_xuat_bo = gia_buon_catalog
                else:
                    gia_xuat_bo = gia_le_catalog
                
                for loai_gia_nguon, so_luong in plan["chi_tiet"]:
                    # Trừ từ DauKyXuatBo trước (FIFO - nhập sớm nhất xuất trước)
                    c.execute(
                        "SELECT id, so_luong, gia, ngay FROM DauKyXuatBo WHERE ten_sanpham=? AND loai_gia=? ORDER BY ngay ASC, id ASC",
                        (ten, loai_gia_nguon)
                    )
                    dauky_rows = c.fetchall()
                    
                    sl_can_tru = so_luong
                    for row_id, sl_row, gia_ban_dauky, ngay_dauky in dauky_rows:
                        if sl_can_tru <= 0:
                            break
                        tru = min(sl_row, sl_can_tru)
                        
                        # Tính chênh lệch: Giá bán - Giá xuất bổ
                        chenh_lech_don_vi = gia_ban_dauky - gia_xuat_bo
                        chenh_lech_phan = chenh_lech_don_vi * tru
                        tong_chenh_lech += chenh_lech_phan
                        
                        if chenh_lech_phan != 0:
                            chenh_lech_chi_tiet.append({
                                "ten": ten,
                                "nguon": f"Đầu kỳ ({loai_gia_nguon})",
                                "sl": tru,
                                "gia_ban": gia_ban_dauky,
                                "gia_xuat": gia_xuat_bo,
                                "chenh_lech": chenh_lech_phan
                            })
                        
                            # Lưu vào bảng ChenhLechXuatBo
                            c.execute("SELECT id FROM SanPham WHERE ten=?", (ten,))
                            sp_row = c.fetchone()
                            if sp_row:
                                from datetime import datetime
                                sanpham_id = sp_row[0]
                                
                                # Xác định giá mới/cũ dựa trên lịch sử thay đổi giá
                                # Lấy lần thay đổi giá gần nhất cho loại giá này
                                c.execute(
                                    """
                                    SELECT gia_moi, ngay_thay_doi 
                                    FROM LichSuGia 
                                    WHERE sanpham_id=? AND loai_gia=? 
                                    ORDER BY ngay_thay_doi DESC 
                                    LIMIT 1
                                    """,
                                    (sanpham_id, loai_gia_nguon)
                                )
                                lich_su = c.fetchone()
                                
                                if lich_su:
                                    gia_moi_nhat, ngay_doi = lich_su
                                    # So sánh giá bán với giá mới nhất trong lịch sử
                                    is_gia_moi = 1 if abs(float(gia_ban_dauky) - float(gia_moi_nhat)) < 1e-6 else 0
                                else:
                                    # Không có lịch sử thay đổi, coi như giá hiện tại
                                    if loai_gia_nguon == "vip":
                                        gia_hien_tai = gia_vip_catalog
                                    elif loai_gia_nguon == "buon":
                                        gia_hien_tai = gia_buon_catalog
                                    else:
                                        gia_hien_tai = gia_le_catalog
                                    is_gia_moi = 1 if abs(float(gia_ban_dauky) - float(gia_hien_tai)) < 1e-6 else 0
                                
                                c.execute(
                                    """
                                    INSERT INTO ChenhLechXuatBo 
                                    (user_id, sanpham_id, ten_sanpham, so_luong, loai_gia_nguon, 
                                     loai_gia_xuat, gia_ban, gia_xuat, chenh_lech, ngay, is_gia_moi)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """,
                                    (self.user_id, sanpham_id, ten, tru, loai_gia_nguon,
                                     loai_gia_xuat, gia_ban_dauky, gia_xuat_bo, chenh_lech_phan,
                                     datetime.now().strftime("%Y-%m-%d %H:%M:%S"), is_gia_moi)
                                )
                        
                        c.execute(
                            "UPDATE DauKyXuatBo SET so_luong=so_luong-? WHERE id=?",
                            (tru, row_id)
                        )
                        c.execute(
                            "DELETE FROM DauKyXuatBo WHERE id=? AND so_luong<=0",
                            (row_id,)
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
                            (ten, loai_gia_nguon)
                        )
                        hd_rows = c.fetchall()
                        
                        for row_id, sl_row, gia_ban_hd, ngay_ban in hd_rows:
                            if sl_can_tru <= 0:
                                break
                            tru = min(sl_row, sl_can_tru)
                            
                            # Tính chênh lệch: Giá bán - Giá xuất bổ
                            chenh_lech_don_vi = gia_ban_hd - gia_xuat_bo
                            chenh_lech_phan = chenh_lech_don_vi * tru
                            tong_chenh_lech += chenh_lech_phan
                            
                            if chenh_lech_phan != 0:
                                chenh_lech_chi_tiet.append({
                                    "ten": ten,
                                    "nguon": f"Hóa đơn ({loai_gia_nguon})",
                                    "sl": tru,
                                    "gia_ban": gia_ban_hd,
                                    "gia_xuat": gia_xuat_bo,
                                    "chenh_lech": chenh_lech_phan
                                })
                            
                                # Lưu vào bảng ChenhLechXuatBo
                                c.execute("SELECT id FROM SanPham WHERE ten=?", (ten,))
                                sp_row = c.fetchone()
                                if sp_row:
                                    from datetime import datetime
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
                                        (sanpham_id, loai_gia_nguon)
                                    )
                                    lich_su = c.fetchone()
                                    
                                    if lich_su:
                                        gia_moi_nhat, ngay_doi = lich_su
                                        is_gia_moi = 1 if abs(float(gia_ban_hd) - float(gia_moi_nhat)) < 1e-6 else 0
                                    else:
                                        # Không có lịch sử, so với giá catalog hiện tại
                                        if loai_gia_nguon == "vip":
                                            gia_hien_tai = gia_vip_catalog
                                        elif loai_gia_nguon == "buon":
                                            gia_hien_tai = gia_buon_catalog
                                        else:
                                            gia_hien_tai = gia_le_catalog
                                        is_gia_moi = 1 if abs(float(gia_ban_hd) - float(gia_hien_tai)) < 1e-6 else 0
                                    
                                    c.execute(
                                        """
                                        INSERT INTO ChenhLechXuatBo 
                                        (user_id, sanpham_id, ten_sanpham, so_luong, loai_gia_nguon, 
                                         loai_gia_xuat, gia_ban, gia_xuat, chenh_lech, ngay, is_gia_moi)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                        """,
                                        (self.user_id, sanpham_id, ten, tru, loai_gia_nguon,
                                         loai_gia_xuat, gia_ban_hd, gia_xuat_bo, chenh_lech_phan,
                                         datetime.now().strftime("%Y-%m-%d %H:%M:%S"), is_gia_moi)
                                    )
                            
                            c.execute(
                                "UPDATE ChiTietHoaDon SET xuat_hoa_don=1, so_luong=so_luong-? WHERE id=?",
                                (tru, row_id)
                            )
                            sl_can_tru -= tru
            
            # Tạo bản ghi xuất dư (nếu có)
            from datetime import datetime
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
                        (self.user_id, sp_id, ten, sl_du, loai_gia_du, ngay)
                    )
            
            # KHÔNG commit ngay - chờ user xác nhận
            
            # Hiển thị chênh lệch (nếu có) và CHỜ XÁC NHẬN
            if chenh_lech_chi_tiet:
                dialog = QDialog(self)
                dialog.setWindowTitle("Xác nhận xuất bổ - Chênh lệch công đoàn")
                dialog.resize(600, 400)
                layout = QVBoxLayout()
                
                layout.addWidget(QLabel("<b>Chi tiết chênh lệch:</b>"))
                
                for item in chenh_lech_chi_tiet:
                    layout.addWidget(QLabel(
                        f"• {item['ten']} ({item['nguon']}): {item['sl']} sp x "
                        f"({format_price(item['gia_ban'])} - {format_price(item['gia_xuat'])}) = "
                        f"{format_price(item['chenh_lech'])}"
                    ))
                
                layout.addWidget(QLabel(f"\n<b>--- Tổng chênh lệch: {format_price(tong_chenh_lech)} ---</b>"))
                
                if tong_chenh_lech != 0:
                    layout.addWidget(QLabel(f"\n⚠️ Sẽ trừ {format_price(tong_chenh_lech)} vào số dư của bạn"))
                
                layout.addWidget(QLabel("\n<i>Bấm OK để xác nhận xuất bổ, hoặc đóng cửa sổ để hủy.</i>"))
                
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
                    if tong_chenh_lech != 0:
                        c.execute(
                            "UPDATE Users SET so_du = so_du - ? WHERE id = ?",
                            (tong_chenh_lech, self.user_id)
                        )
                    conn.commit()
                    show_success(self, f"Xuất bổ thành công!\nĐã trừ {format_price(tong_chenh_lech)} vào số dư")
                else:
                    # User đóng dialog hoặc bấm Hủy → Rollback
                    conn.rollback()
                    show_info(self, "Đã hủy", "Đã hủy thao tác xuất bổ")
                    conn.close()
                    return
            else:
                # Không có chênh lệch → Commit luôn
                conn.commit()
                show_success(self, "Xuất bổ thành công!\n(Không có chênh lệch)")
            
            # Làm mới
            self.load_xuatbo()
            self.xuat_bo_table.setRowCount(0)
            for _ in range(5):
                self.them_dong_xuat_bo()
        
        except Exception as e:
            conn.rollback()
            show_error(self, "Lỗi", f"Lỗi khi xuất bổ: {e}")
        finally:
            conn.close()
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
            show_error(self, "Lỗi", "Không có sản phẩm để xuất")
            return

        # Kiểm tra số lượng có sẵn và tính chênh lệch công đoạn
        chenh_lech_total = 0
        chenh_lech_items = []

        # Trước khi duyệt chi tiết, kiểm tra ngưỡng SYS cho từng sản phẩm (không cho xuất vượt SYS)
        # Sử dụng đúng công thức của tab Báo cáo để đảm bảo đồng nhất số liệu.
        def tinh_sys(ten):
            return self.sys_baocao_by_ten(ten)

        tong_theo_sp = {}
        for it in items:
            ten_it = it["ten"]
            tong_theo_sp[ten_it] = tong_theo_sp.get(ten_it, 0) + it["so_luong"]
        vuot_sys = []
        for ten_sp, sl_yeu_cau in tong_theo_sp.items():
            sys_val = tinh_sys(ten_sp)
            if sl_yeu_cau > sys_val:
                vuot_sys.append((ten_sp, sl_yeu_cau, sys_val))
        if vuot_sys:
            msg = "\n".join(
                [
                    f"- {ten}: yêu cầu {sl} > SYS {format_price(sys)}"
                    for ten, sl, sys in vuot_sys
                ]
            )
            show_error(self, "Vượt SYS", f"Không thể xuất vì vượt SYS:\n{msg}")
            return

        need_over_accept = []

        for item in items:
            ten = item["ten"]
            sl_xuat = item["so_luong"]
            loai_gia_xuat = item["loai_gia"]

            # Lấy thông tin sản phẩm
            from products import tim_sanpham

            sp_info = tim_sanpham(ten)
            if not sp_info:
                show_error(self, "Lỗi", f"Sản phẩm '{ten}' không tồn tại")
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
                    # Đánh dấu cần chấp nhận xuất dư
                    item["need_over_accept"] = True
                    item["over_qty"] = sl_xuat - sl_le
                    need_over_accept.append((ten, sl_xuat, sl_le))
                # Giá lẻ không có chênh lệch công đoạn

            elif loai_gia_xuat == "buon":
                sl_can_tru = sl_xuat
                print(
                    f"DEBUG BUON - Sản phẩm: {ten}, Cần xuất: {sl_xuat}, Buôn có: {sl_buon}, Lẻ có: {sl_le}"
                )
                if sl_buon >= sl_can_tru:
                    # Đủ từ bảng buôn
                    print(f"DEBUG BUON - Đủ từ bảng buôn")
                    pass
                else:
                    # Hỏi có lấy thêm từ bảng lẻ không
                    thieu = sl_can_tru - sl_buon
                    print(f"DEBUG BUON - Thiếu {thieu}, cần lấy từ lẻ")
                    reply = QMessageBox.question(
                        self,
                        "Thiếu số lượng",
                        f"Giá buôn chỉ còn {sl_buon}. Cần lấy thêm {thieu} từ bảng giá lẻ?\n(Giá lẻ hiện có: {sl_le})",
                        QMessageBox.Yes | QMessageBox.No,
                    )
                    if reply != QMessageBox.Yes:
                        return
                    # Lấy tối đa từ bảng lẻ, phần còn thiếu sẽ là xuất dư nếu được chấp nhận
                    lay_tu_le = min(sl_le, thieu)
                    item["loai_gia_phu"] = "le"
                    item["so_luong_phu"] = lay_tu_le
                    if lay_tu_le < thieu:
                        du = thieu - lay_tu_le
                        item["need_over_accept"] = True
                        item["over_qty"] = du
                        need_over_accept.append((ten, sl_xuat, sl_buon + sl_le))
                    print(f"DEBUG BUON - Sẽ xuất {sl_buon} từ buôn và {thieu} từ lẻ")

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
                        # Lấy tối đa từ lẻ, phần thiếu là xuất dư
                        item["loai_gia_phu2"] = "le"
                        item["so_luong_phu2"] = sl_le
                        du = sl_tru_le - sl_le
                        item["need_over_accept"] = True
                        item["over_qty"] = du
                        need_over_accept.append(
                            (ten, sl_xuat, sl_vip + sl_buon + sl_le)
                        )
                    else:
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

        # Nếu có dòng cần chấp nhận xuất dư, hỏi xác nhận trước
        if need_over_accept:
            details = [
                f"- {ten}: cần {can}, hiện có {co}. Cho phép xuất dư phần thiếu?"
                for ten, can, co in need_over_accept
            ]
            reply_over = QMessageBox.question(
                self,
                "Xác nhận xuất dư",
                "\n".join(details),
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply_over != QMessageBox.Yes:
                return
            for it in items:
                if it.get("need_over_accept"):
                    it["allow_over_export"] = True

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
        from db import ket_noi

        conn = ket_noi()
        c = conn.cursor()
        try:
            for item in items:
                ten = item["ten"]
                loai_gia = item["loai_gia"]
                so_luong_xuat = item["so_luong"]
                # Truyền thông tin về loại giá phụ nếu có
                loai_gia_phu = item.get("loai_gia_phu")
                so_luong_phu = item.get("so_luong_phu", 0)
                loai_gia_phu2 = item.get("loai_gia_phu2")
                so_luong_phu2 = item.get("so_luong_phu2", 0)

                # Kiểm tra số lượng đầu kỳ còn lại
                c.execute(
                    "SELECT id, so_luong FROM DauKyXuatBo WHERE ten_sanpham=? AND loai_gia=? ORDER BY id ASC",
                    (ten, loai_gia),
                )
                dauky_rows = c.fetchall()
                sl_dauky_con = sum([r[1] for r in dauky_rows])
                sl_xuat_dauky = min(so_luong_xuat, sl_dauky_con)
                sl_xuat_hoadon = so_luong_xuat - sl_xuat_dauky

                # Nếu có số lượng đầu kỳ, trừ trong DauKyXuatBo
                if sl_xuat_dauky > 0:
                    sl_can_tru = sl_xuat_dauky
                    for r in dauky_rows:
                        if sl_can_tru <= 0:
                            break
                        row_id, sl_row = r
                        tru = min(sl_row, sl_can_tru)
                        # Trừ số lượng
                        c.execute(
                            "UPDATE DauKyXuatBo SET so_luong=so_luong-? WHERE id=?",
                            (tru, row_id),
                        )
                        # Nếu hết số lượng thì xóa dòng
                        c.execute(
                            "DELETE FROM DauKyXuatBo WHERE id=? AND so_luong<=0",
                            (row_id,),
                        )
                        sl_can_tru -= tru

                conn.commit()
        except Exception as e:
            conn.rollback()
            show_error(self, "Lỗi", f"Lỗi khi xử lý đầu kỳ: {e}")
            conn.close()
            return
        finally:
            conn.close()

        # Nếu còn số lượng phải xuất từ hóa đơn
        for item in items:
            ten = item["ten"]
            so_luong_xuat = item["so_luong"]
            loai_gia = item["loai_gia"]
            loai_gia_phu = item.get("loai_gia_phu")
            so_luong_phu = item.get("so_luong_phu", 0)
            loai_gia_phu2 = item.get("loai_gia_phu2")
            so_luong_phu2 = item.get("so_luong_phu2", 0)

            # Recalculate xuất hóa đơn - kiểm tra lại sau khi đã trừ đầu kỳ
            conn = ket_noi()
            c = conn.cursor()
            c.execute(
                "SELECT id, so_luong FROM DauKyXuatBo WHERE ten_sanpham=? AND loai_gia=? ORDER BY id ASC",
                (ten, loai_gia),
            )
            dauky_rows = c.fetchall()
            conn.close()
            sl_dauky_con = sum([r[1] for r in dauky_rows])
            sl_xuat_dauky = min(so_luong_xuat, sl_dauky_con)
            sl_xuat_hoadon = so_luong_xuat - sl_xuat_dauky

            print(f"DEBUG XUẤT - {ten} ({loai_gia}):")
            print(f"  - Yêu cầu xuất: {so_luong_xuat}")
            print(
                f"  - Đã xuất từ đầu kỳ: {so_luong_xuat - sl_dauky_con if sl_dauky_con < so_luong_xuat else so_luong_xuat}"
            )
            print(f"  - Còn phải xuất từ hóa đơn: {sl_xuat_hoadon}")

            # Nếu còn số lượng phải xuất từ hóa đơn, gọi hàm xuất bổ cũ
            if sl_xuat_hoadon > 0:
                sp_info = tim_sanpham(ten)
                if not sp_info:
                    errors.append(f"{ten}: Không tìm thấy thông tin sản phẩm")
                    continue
                sp = sp_info[0]
                gia_le = float(sp[2])
                gia_buon = float(sp[3])
                gia_vip = float(sp[4])
                # Với VIP, tính chênh lệch cho từng phần theo công thức mới
                if loai_gia == "vip":
                    chenh_lech = 0
                    chenh_buon = gia_buon - gia_vip
                    chenh_le = gia_le - gia_vip
                else:
                    chenh_lech = chenh_lech_total
                if loai_gia == "vip":
                    chenh_lech_final = chenh_lech
                else:
                    chenh_lech_final = chenh_lech_total
                # Kiểm tra xem có cho phép xuất dư không
                if item.get("allow_over_export"):
                    # Tính số lượng thực tế có thể xuất từ hóa đơn (bao gồm cả loại giá phụ)
                    try:
                        conn2 = ket_noi()
                        c2 = conn2.cursor()

                        # QUAN TRỌNG: sl_xuat_hoadon đã TRỪ ĐI phần xuất từ đầu kỳ rồi
                        # Nên chỉ cần xuất TỐI ĐA là sl_xuat_hoadon, không được vượt quá!

                        # Tính số lượng thực tế cần xuất từ loại giá chính
                        # (phần còn lại sau khi đã trừ từ loại giá phụ nếu có)
                        sl_can_xuat_chinh = sl_xuat_hoadon
                        if loai_gia_phu and so_luong_phu > 0:
                            sl_can_xuat_chinh -= so_luong_phu
                        if loai_gia_phu2 and so_luong_phu2 > 0:
                            sl_can_xuat_chinh -= so_luong_phu2

                        # Đảm bảo không âm
                        sl_can_xuat_chinh = max(0, sl_can_xuat_chinh)

                        # Số lượng hóa đơn còn lại có thể xuất theo loại giá chính
                        c2.execute(
                            """
                            SELECT COALESCE(SUM(c.so_luong), 0) FROM ChiTietHoaDon c
                            JOIN SanPham s ON c.sanpham_id = s.id
                            WHERE s.ten=? AND c.loai_gia=? AND c.xuat_hoa_don=0
                            """,
                            (ten, loai_gia),
                        )
                        sl_hd_chinh_total = c2.fetchone()[0] or 0
                        # Giới hạn số lượng xuất từ loại giá chính
                        sl_hd_chinh = min(sl_can_xuat_chinh, sl_hd_chinh_total)

                        # Số lượng từ loại giá phụ (nếu có)
                        sl_hd_phu = 0
                        if loai_gia_phu and so_luong_phu > 0:
                            c2.execute(
                                """
                                SELECT COALESCE(SUM(c.so_luong), 0) FROM ChiTietHoaDon c
                                JOIN SanPham s ON c.sanpham_id = s.id
                                WHERE s.ten=? AND c.loai_gia=? AND c.xuat_hoa_don=0
                                """,
                                (ten, loai_gia_phu),
                            )
                            sl_hd_phu_total = c2.fetchone()[0] or 0
                            sl_hd_phu = min(so_luong_phu, sl_hd_phu_total)

                        # Số lượng từ loại giá phụ 2 (nếu có)
                        sl_hd_phu2 = 0
                        if loai_gia_phu2 and so_luong_phu2 > 0:
                            c2.execute(
                                """
                                SELECT COALESCE(SUM(c.so_luong), 0) FROM ChiTietHoaDon c
                                JOIN SanPham s ON c.sanpham_id = s.id
                                WHERE s.ten=? AND c.loai_gia=? AND c.xuat_hoa_don=0
                                """,
                                (ten, loai_gia_phu2),
                            )
                            sl_hd_phu2_total = c2.fetchone()[0] or 0
                            sl_hd_phu2 = min(so_luong_phu2, sl_hd_phu2_total)

                        conn2.close()

                        # Tổng số lượng có thể xuất từ hóa đơn
                        sl_co_the_xuat = sl_hd_chinh + sl_hd_phu + sl_hd_phu2

                        # Debug log
                        print(f"DEBUG XUẤT DƯ - {ten}:")
                        print(
                            f"  - sl_xuat_hoadon (sau khi trừ đầu kỳ): {sl_xuat_hoadon}"
                        )
                        print(f"  - sl_can_xuat_chinh: {sl_can_xuat_chinh}")
                        print(
                            f"  - sl_hd_chinh ({loai_gia}): {sl_hd_chinh} / {sl_hd_chinh_total}"
                        )
                        print(f"  - sl_hd_phu ({loai_gia_phu}): {sl_hd_phu}")
                        print(f"  - sl_hd_phu2 ({loai_gia_phu2}): {sl_hd_phu2}")
                        print(f"  - sl_co_the_xuat (TONG THUC TE): {sl_co_the_xuat}")

                        # Tính phần dư
                        du = sl_xuat_hoadon - sl_co_the_xuat
                        print(f"  - du (SO AM CAN TAO): {du}")

                        # Xuất phần có từ hóa đơn
                        # QUAN TRỌNG: xuat_bo_san_pham_theo_ten ĐÃ TỰ ĐỘNG XỬ LÝ loai_gia_phu!
                        # Không được gọi nhiều lần riêng biệt, sẽ bị xuất trùng!
                        if sl_co_the_xuat > 0:
                            # Gọi MỘT LẦN với số lượng THỰC TẾ có thể xuất (không phải tổng yêu cầu)
                            ok, m2 = xuat_bo_san_pham_theo_ten(
                                ten,
                                loai_gia,
                                sl_co_the_xuat,  # CHỈ XUẤT PHẦN CÓ SẴN (đã tính cả phụ)
                                self.user_id,
                                chenh_lech_final,
                                loai_gia_phu if sl_hd_phu > 0 else None,
                                sl_hd_phu if sl_hd_phu > 0 else 0,
                                loai_gia_phu2 if sl_hd_phu2 > 0 else None,
                                sl_hd_phu2 if sl_hd_phu2 > 0 else 0,
                            )
                            if not ok:
                                errors.append(f"{ten}: {m2}")
                                continue

                        # Phần dư đã được tính ở trên: du = sl_xuat_hoadon - sl_co_the_xuat
                        # Nếu du > 0 nghĩa là xuất vượt quá số có sẵn → tạo XuatDu tracking
                        if du > 0:
                            # Tạo bản ghi XuatDu cho loại giá chính
                            conn3 = ket_noi()
                            c3 = conn3.cursor()
                            try:
                                c3.execute("SELECT id FROM SanPham WHERE ten=?", (ten,))
                                row3 = c3.fetchone()
                                if row3:
                                    sp_id3 = row3[0]
                                    from datetime import datetime

                                    ngay3 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                                    # INSERT vào bảng XuatDu
                                    c3.execute(
                                        """
                                        INSERT INTO XuatDu (user_id, sanpham_id, ten_sanpham, so_luong, loai_gia, ngay)
                                        VALUES (?, ?, ?, ?, ?, ?)
                                        """,
                                        (
                                            self.user_id,
                                            sp_id3,
                                            ten,
                                            du,
                                            loai_gia,
                                            ngay3,
                                        ),
                                    )

                                    # Log phần dư vào LogKho
                                    c3.execute(
                                        "INSERT INTO LogKho (sanpham_id, user_id, ngay, hanh_dong, so_luong, ton_truoc, ton_sau, gia_ap_dung, chenh_lech_cong_doan, loai_gia) VALUES (?, ?, ?, 'xuatbo', ?, 0, 0, 0, ?, ?)",
                                        (
                                            sp_id3,
                                            self.user_id,
                                            ngay3,
                                            du,
                                            chenh_lech_final,
                                            loai_gia,
                                        ),
                                    )

                                    # Trừ số dư phần chênh lệch cho phần dư
                                    c3.execute(
                                        "UPDATE Users SET so_du = so_du - ? WHERE id = ?",
                                        (du * chenh_lech_final, self.user_id),
                                    )

                                    conn3.commit()
                                    print(
                                        f"XUAT_DU: Tạo {du} xuất dư {loai_gia} cho {ten}"
                                    )
                                conn3.close()
                            except Exception as e3:
                                try:
                                    conn3.rollback()
                                    conn3.close()
                                except Exception:
                                    pass
                                errors.append(f"{ten}: Lỗi khi ghi log xuất dư: {e3}")
                    except Exception as e2:
                        errors.append(f"{ten}: Lỗi khi xử lý xuất dư: {e2}")
                else:
                    # Xuất bình thường, không cho phép xuất dư
                    success, msg = xuat_bo_san_pham_theo_ten(
                        ten,
                        loai_gia,
                        sl_xuat_hoadon,
                        self.user_id,
                        chenh_lech_final,
                        loai_gia_phu,
                        so_luong_phu,
                        loai_gia_phu2,
                        so_luong_phu2,
                    )
                    if not success:
                        errors.append(f"{ten}: {msg}")
        conn.close()

        if errors:
            show_error(self, "Lỗi", "\n".join(errors))
        else:
            show_success(self, "Xuất bổ thành công")

        # Làm mới
        self.load_xuatbo()
        self.xuat_bo_table.setRowCount(0)
        for _ in range(5):
            self.them_dong_xuat_bo()

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

    def init_tab_cong_doan(self):
        layout = QVBoxLayout()

        # Lọc theo ngày và username
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("User:"))
        self.cd_user_combo = QComboBox()
        self.cd_user_combo.addItem("Tất cả", None)
        from users import lay_tat_ca_user

        try:
            for uid, uname, role, so_du in lay_tat_ca_user():
                self.cd_user_combo.addItem(f"{uname} (ID: {uid})", uid)
        except Exception:
            pass
        filter_layout.addWidget(self.cd_user_combo)

        filter_layout.addWidget(QLabel("Từ ngày:"))
        self.tu_ngay_edit = QDateEdit()
        self.tu_ngay_edit.setCalendarPopup(True)
        self.tu_ngay_edit.setDate(QDate.currentDate().addMonths(-1))
        filter_layout.addWidget(self.tu_ngay_edit)

        filter_layout.addWidget(QLabel("Đến ngày:"))
        self.den_ngay_edit = QDateEdit()
        self.den_ngay_edit.setCalendarPopup(True)
        self.den_ngay_edit.setDate(QDate.currentDate())
        filter_layout.addWidget(self.den_ngay_edit)

        btn_load_cd = QPushButton("Tải báo cáo")
        btn_load_cd.clicked.connect(self.load_bao_cao_cong_doan)
        filter_layout.addWidget(btn_load_cd)

        layout.addLayout(filter_layout)

        # Bảng công đoàn với TreeWidget để hiển thị phân cấp
        from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
        from PyQt5.QtCore import Qt
        
        self.tree_cong_doan = QTreeWidget()
        self.tree_cong_doan.setColumnCount(7)
        self.tree_cong_doan.setHeaderLabels(
            [
                "User/Chi tiết",
                "Ngày",
                "Sản phẩm",
                "Số lượng",
                "Tổng giá bán",
                "Tổng giá xuất",
                "Chênh lệch",
            ]
        )
        self.tree_cong_doan.setAlternatingRowColors(True)
        for i in range(7):
            self.tree_cong_doan.resizeColumnToContents(i)
        layout.addWidget(self.tree_cong_doan)

        # Tổng tiền chênh lệch
        self.lbl_tong_cd = QLabel("Tổng chênh lệch: 0")
        layout.addWidget(self.lbl_tong_cd)

        # Các nút
        btn_layout = QHBoxLayout()
        btn_chuyen_tien_cd = QPushButton("Chuyển tiền công đoàn")
        btn_chuyen_tien_cd.clicked.connect(self.chuyen_tien_cong_doan_click)
        btn_layout.addWidget(btn_chuyen_tien_cd)

        btn_print_cd = QPushButton("In báo cáo")
        btn_print_cd.clicked.connect(self.print_bao_cao_cong_doan)
        btn_layout.addWidget(btn_print_cd)

        layout.addLayout(btn_layout)

        self.tab_cong_doan.setLayout(layout)

    def load_bao_cao_cong_doan(self):
        """Load báo cáo công đoàn từ bảng ChenhLechXuatBo - hiển thị theo nhóm xuất bổ"""
        from PyQt5.QtWidgets import QTreeWidgetItem
        
        tu_ngay = self.tu_ngay_edit.date().toString("yyyy-MM-dd")
        den_ngay = self.den_ngay_edit.date().toString("yyyy-MM-dd")
        user_id = self.cd_user_combo.currentData()

        try:
            conn = ket_noi()
            c = conn.cursor()

            base_sql = """
                SELECT 
                    u.username,
                    cl.user_id,
                    datetime(cl.ngay) as ngay_xuat,
                    cl.ten_sanpham,
                    cl.loai_gia_xuat,
                    cl.loai_gia_nguon,
                    COALESCE(cl.is_gia_moi, 0) as is_gia_moi,
                    COALESCE(cl.gia_ban, 0) as gia_ban,
                    COALESCE(cl.gia_xuat, 0) as gia_xuat,
                    COALESCE(cl.so_luong, 0) as so_luong,
                    (COALESCE(cl.gia_ban, 0) * COALESCE(cl.so_luong, 0)) as tong_gia_ban,
                    (COALESCE(cl.gia_xuat, 0) * COALESCE(cl.so_luong, 0)) as tong_gia_xuat,
                    COALESCE(cl.chenh_lech, 0) as chenh_lech
                FROM ChenhLechXuatBo cl
                JOIN Users u ON cl.user_id = u.id
                WHERE date(cl.ngay) >= ? AND date(cl.ngay) <= ?
            """
            params = [tu_ngay, den_ngay]

            if user_id is not None:
                base_sql += " AND cl.user_id = ?"
                params.append(user_id)

            base_sql += """
                ORDER BY cl.ngay DESC, u.username, cl.ten_sanpham, cl.loai_gia_nguon, COALESCE(cl.is_gia_moi,0)
            """

            c.execute(base_sql, params)
            rows = c.fetchall()

            self.tree_cong_doan.clear()

            from collections import defaultdict
            groups = defaultdict(list)
            for r in rows:
                # r = (username, user_id, ngay_xuat, ten_sp, loai_gia_xuat, loai_gia_nguon, 
                #      is_gia_moi, gia_ban, gia_xuat, so_luong, tong_gia_ban, tong_gia_xuat, chenh_lech)
                # Index:  0         1        2          3       4              5
                #         6           7        8         9         10            11              12
                key = (r[0], r[2], r[3], r[4])  # username, ngay_xuat, ten_sp, loai_gia_xuat
                groups[key].append(r)

            tong_chenh_lech_tat_ca = 0
            for key, details in groups.items():
                username, ngay_xuat, ten_sp, loai_gia_xuat = key
                
                # Tính tổng cho dòng cha từ các dòng con
                tong_sl = sum(d[9] for d in details)           # d[9] = so_luong
                tong_gia_ban = sum(d[10] for d in details)     # d[10] = tong_gia_ban
                tong_gia_xuat = sum(d[11] for d in details)    # d[11] = tong_gia_xuat
                tong_chenh_lech = sum(d[12] for d in details)  # d[12] = chenh_lech
                tong_chenh_lech_tat_ca += tong_chenh_lech

                parent = QTreeWidgetItem(self.tree_cong_doan)
                parent.setText(0, username)
                parent.setText(1, str(ngay_xuat))
                parent.setText(2, ten_sp)
                parent.setText(3, f"{int(tong_sl)}")
                parent.setText(4, format_price(tong_gia_ban))
                parent.setText(5, format_price(tong_gia_xuat))
                parent.setText(6, format_price(tong_chenh_lech))
                for col in range(7):
                    font = parent.font(col)
                    font.setBold(True)
                    parent.setFont(col, font)

                # Tạo dòng con
                for detail in details:
                    loai_gia_nguon = detail[5]
                    is_gia_moi = int(detail[6]) if detail[6] is not None else 0
                    gia_ban = detail[7]
                    gia_xuat = detail[8]
                    sl = detail[9]
                    gia_ban_tong = detail[10]
                    gia_xuat_tong = detail[11]
                    chenh_lech = detail[12]
                    
                    child = QTreeWidgetItem(parent)
                    nhan = f"{loai_gia_nguon.upper()} {'MỚI' if is_gia_moi==1 else 'CŨ'}"
                    child.setText(0, nhan)
                    child.setText(1, "")
                    child.setText(2, "")
                    child.setText(3, f"{int(sl)}")
                    child.setText(4, f"{format_price(gia_ban)}/sp → {format_price(gia_ban_tong)}")
                    child.setText(5, f"{format_price(gia_xuat)}/sp → {format_price(gia_xuat_tong)}")
                    child.setText(6, format_price(chenh_lech))
                
                parent.setExpanded(True)

            self.lbl_tong_cd.setText(
                f"Tổng chênh lệch: {format_price(tong_chenh_lech_tat_ca)}"
            )
            for i in range(7):
                self.tree_cong_doan.resizeColumnToContents(i)
            conn.close()
        except Exception as e:
            show_error(self, "Lỗi", f"Lỗi tải báo cáo công đoàn: {e}")

    def chuyen_tien_cong_doan_click(self):
        # Dialog chuyển tiền công đoàn
        dialog = QDialog(self)
        dialog.setWindowTitle("Chuyển tiền công đoàn")
        layout = QVBoxLayout()

        # Dùng user hiện tại đang đăng nhập làm nguồn tiền
        from users import lay_tat_ca_user

        users = lay_tat_ca_user()
        current_user_name = None
        for user in users:
            if user[0] == self.user_id:  # user[0] là ID
                current_user_name = user[1]  # user[1] là username
                break

        if not current_user_name:
            current_user_name = "User hiện tại"

        layout.addWidget(QLabel(f"Từ user: {current_user_name}"))

        layout.addWidget(QLabel("Đến user (nhập tên):"))
        den_user_edit = QLineEdit()
        den_user_edit.setPlaceholderText("Nhập tên người nhận...")
        layout.addWidget(den_user_edit)

        layout.addWidget(QLabel("Số tiền:"))
        so_tien_edit = QLineEdit()
        so_tien_edit.setValidator(QDoubleValidator())
        layout.addWidget(so_tien_edit)

        layout.addWidget(QLabel("Nội dung:"))
        noi_dung_edit = QLineEdit()
        noi_dung_edit.setPlaceholderText("Chuyển tiền công đoàn...")
        layout.addWidget(noi_dung_edit)

        btn_ok = QPushButton("Xác nhận")
        btn_ok.clicked.connect(dialog.accept)
        layout.addWidget(btn_ok)

        dialog.setLayout(layout)

        if dialog.exec_() != QDialog.Accepted:
            return

        den_user_name = den_user_edit.text().strip()
        so_tien_str = so_tien_edit.text()
        noi_dung = noi_dung_edit.text()

        if not den_user_name:
            show_error(self, "Lỗi", "Vui lòng nhập tên người nhận")
            return

        if not so_tien_str:
            show_error(self, "Lỗi", "Vui lòng nhập số tiền")
            return

        try:
            so_tien = float(so_tien_str)
        except Exception as e:
            show_error(self, "Lỗi", f"Số tiền không hợp lệ: {e}")
            return

        # Trừ tiền từ user hiện tại và ghi log
        try:
            from datetime import datetime

            conn = ket_noi()
            c = conn.cursor()

            # Kiểm tra số dư user hiện tại
            c.execute("SELECT so_du FROM Users WHERE id = ?", (self.user_id,))
            result = c.fetchone()
            so_du = result[0] if result else 0

            if so_du < so_tien:
                show_error(
                    self,
                    "Lỗi",
                    f"Số dư không đủ!\nSố dư hiện tại: {format_price(so_du)}\nCần: {format_price(so_tien)}",
                )
                conn.close()
                return

            # Trừ tiền từ user hiện tại
            c.execute(
                "UPDATE Users SET so_du = so_du - ? WHERE id = ?",
                (so_tien, self.user_id),
            )

            # Ghi log vào GiaoDichQuy (không có user_nhan_id vì nhận bằng tay)
            thoi_gian = datetime.now().isoformat()
            ghi_chu_full = (
                f"Chuyển công đoàn cho: {den_user_name}. {noi_dung}"
                if noi_dung
                else f"Chuyển công đoàn cho: {den_user_name}"
            )
            c.execute(
                "INSERT INTO GiaoDichQuy (user_id, user_nhan_id, so_tien, ngay, ghi_chu) VALUES (?, NULL, ?, ?, ?)",
                (self.user_id, so_tien, thoi_gian, ghi_chu_full),
            )

            conn.commit()
            show_success(
                self,
                f"Đã chuyển {format_price(so_tien)} từ {current_user_name} cho {den_user_name}",
            )
            self.load_so_quy()
        except Exception as e:
            conn.rollback()
            show_error(self, "Lỗi", f"Lỗi chuyển tiền: {e}")
        finally:
            conn.close()

    def print_bao_cao_cong_doan(self):
        tu_ngay = self.tu_ngay_edit.date().toString("dd/MM/yyyy")
        den_ngay = self.den_ngay_edit.date().toString("dd/MM/yyyy")

        # Tạo HTML cho báo cáo
        html = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                @page {{ size: A4 landscape; margin: 1cm; }}
                body {{ font-family: Arial; font-size: 11pt; }}
                h2 {{ text-align: center; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ border: 1px solid black; padding: 6px; text-align: left; font-size: 10pt; }}
                th {{ background-color: #f0f0f0; font-weight: bold; }}
                .parent-row {{ background-color: #e6f2ff; font-weight: bold; }}
                .child-row {{ padding-left: 20px; background-color: #f9f9f9; }}
                .total {{ font-weight: bold; text-align: right; margin-top: 10px; font-size: 12pt; }}
            </style>
        </head>
        <body>
            <h2>BÁO CÁO CÔNG ĐOÀN</h2>
            <p>Từ ngày: {tu_ngay} - Đến ngày: {den_ngay}</p>
            <table>
                <tr>
                    <th>User/Chi tiết</th>
                    <th>Ngày</th>
                    <th>Sản phẩm</th>
                    <th>Số lượng</th>
                    <th>Tổng giá bán</th>
                    <th>Tổng giá xuất</th>
                    <th>Chênh lệch</th>
                </tr>
        """

        # Duyệt qua các parent items trong tree
        root = self.tree_cong_doan.invisibleRootItem()
        for i in range(root.childCount()):
            parent = root.child(i)
            
            # Dòng cha (tổng hợp)
            html += '<tr class="parent-row">'
            for col in range(7):
                text = parent.text(col)
                html += f"<td>{text}</td>"
            html += "</tr>"
            
            # Dòng con (chi tiết)
            for j in range(parent.childCount()):
                child = parent.child(j)
                html += '<tr class="child-row">'
                for col in range(7):
                    text = child.text(col)
                    # Thụt lề cho cột đầu tiên của dòng con
                    if col == 0:
                        html += f"<td style='padding-left: 30px;'>{text}</td>"
                    else:
                        html += f"<td>{text}</td>"
                html += "</tr>"

        html += f"""
            </table>
            <p class="total">{self.lbl_tong_cd.text()}</p>
        </body>
        </html>
        """

        # In qua dialog
        from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
        from PyQt5.QtWidgets import QTextEdit

        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)

        if dialog.exec_() == QPrintDialog.Accepted:
            text_edit = QTextEdit()
            text_edit.setHtml(html)
            text_edit.print_(printer)
            show_success(self, "Đã gửi báo cáo đến máy in")

    def init_tab_so_quy(self):
        """Khởi tạo tab Sổ quỹ với 2 tab con: Số dư và Lịch sử giao dịch"""
        # Tạo tab con cho Sổ quỹ: "Số dư" và "Lịch sử giao dịch"
        parent_layout = QVBoxLayout()
        self.so_quy_tabs = QTabWidget()
        parent_layout.addWidget(self.so_quy_tabs)

        # Tab con: Số dư (giữ nguyên giao diện hiện tại)
        self.tab_so_quy_sodu = QWidget()
        sodu_layout = QVBoxLayout()
        
        # Bảng số dư
        self.tbl_soquy = QTableWidget()
        self.tbl_soquy.setColumnCount(4)
        self.tbl_soquy.setHorizontalHeaderLabels(["ID", "Username", "Vai trò", "Số dư"])
        self.setup_table(self.tbl_soquy)
        sodu_layout.addWidget(self.tbl_soquy)
        
        # Nút chuyển tiền
        btn_layout_quy = QHBoxLayout()
        btn_chuyen_tien = QPushButton("Chuyển tiền")
        btn_chuyen_tien.clicked.connect(self.chuyen_tien_click)
        btn_layout_quy.addWidget(btn_chuyen_tien)
        sodu_layout.addLayout(btn_layout_quy)
        
        self.tab_so_quy_sodu.setLayout(sodu_layout)
        self.so_quy_tabs.addTab(self.tab_so_quy_sodu, "Số dư")

        # Tab con: Lịch sử giao dịch
        self.tab_so_quy_ls = QWidget()
        ls_layout = QVBoxLayout()
        
        # Filter bar: User + Từ ngày + Đến ngày + Tải
        fl = QHBoxLayout()
        from users import lay_tat_ca_user

        self.ls_user_combo = QComboBox()
        self.ls_user_combo.addItem("Tất cả", None)
        try:
            for uid, uname, role, so_du in lay_tat_ca_user():
                self.ls_user_combo.addItem(f"{uname} (ID: {uid})", uid)
        except Exception:
            pass
        
        fl.addWidget(QLabel("User:"))
        fl.addWidget(self.ls_user_combo)
        fl.addStretch()
        fl.addWidget(QLabel("Từ ngày:"))
        
        self.ls_tu = QDateEdit()
        self.ls_tu.setCalendarPopup(True)
        self.ls_tu.setDate(QDate.currentDate().addMonths(-1))
        fl.addWidget(self.ls_tu)
        
        fl.addWidget(QLabel("Đến ngày:"))
        self.ls_den = QDateEdit()
        self.ls_den.setCalendarPopup(True)
        self.ls_den.setDate(QDate.currentDate())
        fl.addWidget(self.ls_den)
        
        # Tự động tải khi thay đổi filter
        self.ls_user_combo.currentIndexChanged.connect(self.load_lich_su_quy)
        self.ls_tu.dateChanged.connect(self.load_lich_su_quy)
        self.ls_den.dateChanged.connect(self.load_lich_su_quy)
        
        ls_layout.addLayout(fl)

        # Bảng lịch sử giao dịch
        self.tbl_ls_quy = QTableWidget()
        self.tbl_ls_quy.setColumnCount(6)
        self.tbl_ls_quy.setHorizontalHeaderLabels(
            ["Thời gian", "Từ user", "Đến user", "Số tiền", "Ca ngày", "Ghi chú"]
        )
        self.setup_table(self.tbl_ls_quy)
        ls_layout.addWidget(self.tbl_ls_quy)
        
        self.tab_so_quy_ls.setLayout(ls_layout)
        self.so_quy_tabs.addTab(self.tab_so_quy_ls, "Lịch sử giao dịch")

        self.tab_so_quy.setLayout(parent_layout)
        # Nạp dữ liệu mặc định
        self.load_so_quy()
        self.load_lich_su_quy()

    def load_lich_su_quy(self):
        # Đọc filter
        uid = self.ls_user_combo.currentData()
        tu = self.ls_tu.date().toString("yyyy-MM-dd")
        den = self.ls_den.date().toString("yyyy-MM-dd")
        # Query DB
        try:
            conn = ket_noi()
            c = conn.cursor()
            base_sql = (
                "SELECT g.id, u.username AS tu_user, un.username AS den_user, "
                "g.so_tien, g.ngay, COALESCE(g.ghi_chu, '') AS ghi_chu, "
                "COALESCE(h.ngay, '') AS ca_ngay, g.hoadon_id "
                "FROM GiaoDichQuy g "
                "LEFT JOIN Users u ON g.user_id = u.id "
                "LEFT JOIN Users un ON g.user_nhan_id = un.id "
                "LEFT JOIN HoaDon h ON g.hoadon_id = h.id "
                "WHERE date(g.ngay) >= ? AND date(g.ngay) <= ?"
            )
            params = [tu, den]
            if uid is not None:
                base_sql += " AND (g.user_id = ? OR g.user_nhan_id = ?)"
                params += [uid, uid]
            base_sql += " ORDER BY g.ngay DESC, g.id DESC"
            c.execute(base_sql, params)
            rows = c.fetchall()
            self.tbl_ls_quy.setRowCount(len(rows))
            for i, r in enumerate(rows):
                # r = (id, tu_user, den_user, so_tien, ngay_nop_tien, ghi_chu, ca_ngay, hoadon_id)
                # Cột 0: Thời gian nộp tiền (ngày giờ đầy đủ)
                try:
                    ngay_nop_str = str(r[4])  # g.ngay - thời gian nộp tiền
                    # Loại bỏ phần microseconds nếu có
                    if "." in ngay_nop_str:
                        ngay_nop_str = ngay_nop_str.split(".")[0]
                    self.tbl_ls_quy.setItem(i, 0, QTableWidgetItem(ngay_nop_str))
                except Exception:
                    self.tbl_ls_quy.setItem(i, 0, QTableWidgetItem(""))

                # Cột 1-3: User và số tiền
                self.tbl_ls_quy.setItem(i, 1, QTableWidgetItem(str(r[1] or "")))
                self.tbl_ls_quy.setItem(i, 2, QTableWidgetItem(str(r[2] or "")))
                try:
                    self.tbl_ls_quy.setItem(
                        i, 3, QTableWidgetItem(format_price(float(r[3])))
                    )
                except Exception:
                    self.tbl_ls_quy.setItem(i, 3, QTableWidgetItem(str(r[3])))

                # Cột 4: Ca ngày - ưu tiên ngày của hóa đơn, nếu không có thì lấy ngày nộp tiền
                try:
                    ca_ngay_str = str(r[6]) if r[6] else str(r[4])  # h.ngay hoặc g.ngay
                    # Chỉ lấy phần ngày (không lấy giờ)
                    if " " in ca_ngay_str:
                        date_only = ca_ngay_str.split(" ")[0]
                    else:
                        date_only = ca_ngay_str
                    self.tbl_ls_quy.setItem(i, 4, QTableWidgetItem(date_only))
                except Exception:
                    self.tbl_ls_quy.setItem(i, 4, QTableWidgetItem(""))

                # Cột 5: Ghi chú
                self.tbl_ls_quy.setItem(i, 5, QTableWidgetItem(str(r[5] or "")))
        except Exception as e:
            show_error(self, "Lỗi", f"Lỗi tải lịch sử quỹ: {e}")
        finally:
            try:
                conn.close()
            except Exception:
                pass

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
        self.to_tien_spins = []
        for mg in MENH_GIA:
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
                    show_success(
                        self,
                        f"Chuyển tiền thành công\nNội dung: {noi_dung}",
                    )
                    self.load_so_quy()  # Tự động làm mới số dư
                    self.load_lich_su_quy()  # Tự động làm mới lịch sử
                    dialog.close()
                else:
                    show_error(self, "Lỗi", msg)
        except Exception as e:
            show_error(self, "Lỗi", f"Dữ liệu không hợp lệ: {e}")

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
                show_success(self, "Đổi mật khẩu thành công")
            else:
                show_error(self, "Lỗi", "Đổi mật khẩu thất bại")

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
            show_success(self, "Thêm sản phẩm thành công")
            self.load_sanpham()
            self.cap_nhat_completer_sanpham()
        else:
            show_error(self, "Lỗi", "Thêm sản phẩm thất bại")

    def nhap_kho_click(self):
        """Nhập kho sản phẩm (chỉ nhập tên và số lượng, giữ nguyên giá và ngưỡng buôn)"""
        # Dialog chọn sản phẩm
        ten_sanpham_list = lay_danh_sach_ten_sanpham()
        if not ten_sanpham_list:
            show_error(self, "Lỗi", "Chưa có sản phẩm nào trong hệ thống")
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
            show_error(self, "Lỗi", f"Sản phẩm '{ten}' không tồn tại")
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
            show_info(
                self,
                "Thành công",
                f"Nhập kho thành công!\nSản phẩm: {ten}\nSố lượng nhập: {so_luong}\nTồn kho cũ: {ton_kho_cu}\nTồn kho mới: {ton_kho_moi}",
            )
            self.load_sanpham()
        else:
            show_error(self, "Lỗi", "Nhập kho thất bại")

    def xoa_sanpham_click(self):
        row = self.tbl_sanpham.currentRow()
        if row < 0:
            show_error(self, "Lỗi", "Chọn một sản phẩm")
            return
        ten_sp = self.tbl_sanpham.item(row, 1).text()
        if xoa_sanpham(ten_sp):
            show_success(self, "Xóa sản phẩm thành công")
            self.load_sanpham()  # Tự động làm mới danh sách sản phẩm
            self.cap_nhat_completer_sanpham()  # Cập nhật autocomplete
        else:
            show_error(self, "Lỗi", "Xóa sản phẩm thất bại")

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
            ten_sanpham = self.tbl_sanpham.item(row, 1).text()
            value = float(item.text().replace(",", ""))
            # ✅ Validate field name to prevent SQL injection
            allowed_fields = ["gia_le", "gia_buon", "gia_vip", "ton_kho"]
            field = allowed_fields[col - 2]
            
            conn = ket_noi()
            c = conn.cursor()
            
            # Lấy giá cũ trước khi cập nhật (chỉ với các trường giá, không phải tồn kho)
            if field in ["gia_le", "gia_buon", "gia_vip"]:
                c.execute(f"SELECT {field} FROM SanPham WHERE id=?", (product_id,))
                old_value = c.fetchone()[0]
                
                # Nếu giá thay đổi, lưu lịch sử
                if abs(float(old_value) - value) > 1e-6:
                    from datetime import datetime
                    loai_gia_map = {"gia_le": "le", "gia_buon": "buon", "gia_vip": "vip"}
                    loai_gia = loai_gia_map[field]
                    
                    c.execute(
                        """
                        INSERT INTO LichSuGia 
                        (sanpham_id, ten_sanpham, loai_gia, gia_cu, gia_moi, user_id, ngay_thay_doi, ghi_chu)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (product_id, ten_sanpham, loai_gia, old_value, value, 
                         self.user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                         "Cập nhật từ tab Sản phẩm")
                    )
            
            c.execute(f"UPDATE SanPham SET {field}=? WHERE id=?", (value, product_id))
            conn.commit()
            conn.close()
        except Exception as e:
            show_error(self, "Lỗi", f"Giá trị không hợp lệ: {e}")

    def import_sanpham_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Chọn file Excel", "", "Excel Files (*.xlsx)"
        )
        if file_path:
            try:
                df = pd.read_excel(file_path)
                # Truyền user_id để lưu lịch sử thay đổi giá
                if import_sanpham_from_dataframe(df, user_id=self.user_id):
                    show_success(
                        self, "Import sản phẩm thành công!\nLịch sử thay đổi giá đã được lưu."
                    )
                    self.load_sanpham()  # Tự động làm mới danh sách sản phẩm
                    self.load_lich_su_gia()  # Tự động làm mới lịch sử giá
                    self.cap_nhat_completer_sanpham()  # Cập nhật autocomplete
                else:
                    show_error(self, "Lỗi", "Import sản phẩm thất bại")
            except Exception as e:
                show_error(self, "Lỗi", f"Lỗi import: {str(e)}")

    def dong_ca_in_pdf(self):
        if not self.nhan_hang_completed:
            show_error(
                self, "Lỗi", "Bạn chưa nhận hàng. Vui lòng nhận hàng trước khi đóng ca."
            )
            return

        from datetime import datetime
        from PyQt5.QtPrintSupport import QPrinter
        from PyQt5.QtGui import QPainter

        # Lấy dữ liệu nhận hàng với chênh lệch
        nhan_hang_data = []
        chenh_lech_data = []
        for row in range(self.tbl_nhan_hang.rowCount()):
            ten_sp = self.tbl_nhan_hang.item(row, 0).text()
            try:
                sl_dem = float(self.tbl_nhan_hang.item(row, 1).text())
            except Exception as e:
                print(f"Warning: Invalid quantity at row {row}: {e}")
                sl_dem = 0
            try:
                ton_db = float(self.tbl_nhan_hang.item(row, 2).text())
            except Exception as e:
                print(f"Warning: Invalid stock at row {row}: {e}")
                ton_db = 0
            try:
                chenh = float(self.tbl_nhan_hang.item(row, 3).text())
            except Exception as e:
                print(f"Warning: Invalid difference at row {row}: {e}")
                chenh = 0
            ghi_chu = (
                self.tbl_nhan_hang.item(row, 4).text()
                if self.tbl_nhan_hang.item(row, 4)
                else ""
            )

            if sl_dem > 0:
                nhan_hang_data.append((ten_sp, sl_dem, ton_db, chenh, ghi_chu))
                if abs(chenh) > 0.001:  # Có chênh lệch
                    chenh_lech_data.append((ten_sp, ton_db, sl_dem, chenh, ghi_chu))

        # Lấy dữ liệu bán hàng từ HÓA ĐƠN CUỐI CÙNG (hóa đơn vừa tạo)
        today = datetime.now().strftime("%Y-%m-%d")
        today_display = datetime.now().strftime("%d/%m/%Y %H:%M")
        from invoices import lay_chi_tiet_hoadon

        # Dùng dict để gộp sản phẩm: key = (tên, loại_gia, giá, xhd)
        sp_dict_xhd = {}  # {(tên, loại_gia, giá): [tổng_sl, tổng_tiền]}
        sp_dict_chua_xhd = {}
        tong_tien_ban = 0
        tong_tien_xhd = 0
        tong_tien_chua_xhd = 0

        # Lấy chi tiết từ hóa đơn cuối cùng (nếu có)
        if self.last_invoice_id:
            chi_tiet = lay_chi_tiet_hoadon(self.last_invoice_id)
            for r in chi_tiet:
                # r = (id, hoadon_id, sanpham_id, ten, so_luong, loai_gia, gia, xuat_hoa_don, gia_le, giam, ghi_chu)
                ten = r[3]
                sl = r[4]
                loai_gia = r[5]
                gia = r[6]
                xhd = r[7]
                giam = r[9] if len(r) > 9 else 0
                tong = sl * gia - giam
                tong_tien_ban += tong

                loai_gia_text = {"le": "Lẻ", "buon": "Buôn", "vip": "VIP"}.get(
                    loai_gia, loai_gia
                )
                key = (ten, loai_gia_text, gia)

                if xhd == 1:
                    if key not in sp_dict_xhd:
                        sp_dict_xhd[key] = [0, 0]
                    sp_dict_xhd[key][0] += sl
                    sp_dict_xhd[key][1] += tong
                    tong_tien_xhd += tong
                else:
                    if key not in sp_dict_chua_xhd:
                        sp_dict_chua_xhd[key] = [0, 0]
                    sp_dict_chua_xhd[key][0] += sl
                    sp_dict_chua_xhd[key][1] += tong
                    tong_tien_chua_xhd += tong

        # Chuyển dict thành list để hiển thị
        sp_da_xhd = [
            (ten, sl, loai_gia, gia, tong)
            for (ten, loai_gia, gia), [sl, tong] in sp_dict_xhd.items()
        ]
        sp_chua_xhd = [
            (ten, sl, loai_gia, gia, tong)
            for (ten, loai_gia, gia), [sl, tong] in sp_dict_chua_xhd.items()
        ]

        # Lấy công đoàn và tiền nộp
        from users import lay_tong_nop_theo_hoadon
        from invoices import lay_danh_sach_hoadon

        # Tính tổng công đoàn từ LogKho
        tong_cong_doan = 0
        try:
            conn = ket_noi()
            c = conn.cursor()
            c.execute(
                "SELECT SUM(chenh_lech_cong_doan) FROM LogKho WHERE date(ngay) = ? AND hanh_dong = 'xuat'",
                (today,),
            )
            result = c.fetchone()
            tong_cong_doan = result[0] if result and result[0] else 0
            conn.close()
        except Exception as e:
            print(f"Warning: Could not load tong_cong_doan: {e}")
            tong_cong_doan = 0

        tong_nop = 0
        # Lấy tiền đã nộp từ hóa đơn cuối cùng
        if self.last_invoice_id:
            tong_nop = lay_tong_nop_theo_hoadon(self.last_invoice_id) or 0

        tong_thieu = tong_tien_ban - tong_nop

        # Show preview dialog
        preview_dialog = QDialog(self)
        preview_dialog.setWindowTitle("Xem trước tổng kết ca")
        preview_dialog.resize(800, 600)
        layout = QVBoxLayout()

        # Create text content
        content = QTextEdit()
        content.setReadOnly(True)

        # Import helper to resolve username
        from users import lay_username

        html_content = f"""
        <html>
        <head>
            <style>
                @page {{
                    size: A4 portrait;
                    margin: 15mm;
                }}
                @media print {{
                    body {{
                        margin: 0;
                        padding: 0;
                    }}
                    .no-print {{
                        display: none;
                    }}
                }}
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    font-size: 10pt;
                    margin: 0;
                    padding: 10px;
                    max-width: 210mm;
                }}
                h1 {{
                    text-align: center;
                    color: #2c3e50;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 8px;
                    margin: 10px 0 15px 0;
                    font-size: 16pt;
                }}
                h2 {{
                    color: #34495e;
                    margin-top: 15px;
                    margin-bottom: 8px;
                    border-left: 3px solid #3498db;
                    padding-left: 8px;
                    font-size: 12pt;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 5px 0 10px 0;
                    font-size: 9pt;
                }}
                th {{
                    background-color: #3498db;
                    color: white;
                    padding: 6px 8px;
                    text-align: left;
                    font-weight: bold;
                    border: 1px solid #2980b9;
                }}
                td {{
                    padding: 5px 8px;
                    border: 1px solid #ddd;
                }}
                tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                .info-box {{
                    background-color: #e8f5e9;
                    padding: 8px;
                    border-left: 3px solid #4caf50;
                    margin: 10px 0;
                    font-size: 9pt;
                }}
                .money {{
                    text-align: right;
                    font-weight: bold;
                }}
                .total-row {{
                    background-color: #3498db !important;
                    color: white;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <h1>BÁO CÁO ĐÓNG CA</h1>
            
            <div class="info-box">
                <strong>Ngày giờ:</strong> {datetime.now().strftime("%d/%m/%Y %H:%M")}<br>
                <strong>Người bán:</strong> {lay_username(self.user_id)} (ID: {self.user_id})
            </div>

            <h2>Danh sách nhận hàng</h2>
        """

        if nhan_hang_data:
            html_content += """
            <table>
                <tr>
                    <th>Sản phẩm</th>
                    <th style="text-align: right;">SL Đếm</th>
                    <th style="text-align: right;">Tồn HT</th>
                    <th style="text-align: right;">Chênh lệch</th>
                    <th>Lý do</th>
                </tr>
            """
            for sp in nhan_hang_data:
                ten, sl_dem, ton_db, chenh, ghi_chu = sp
                chenh_style = (
                    "color: red;"
                    if chenh < 0
                    else ("color: green;" if chenh > 0 else "")
                )
                html_content += f"""
                <tr>
                    <td>{ten}</td>
                    <td class="money">{sl_dem:.0f}</td>
                    <td class="money">{ton_db:.0f}</td>
                    <td class="money" style="{chenh_style}">{chenh:+.0f}</td>
                    <td>{ghi_chu if ghi_chu else '-'}</td>
                </tr>
                """
            html_content += "</table>"
        else:
            html_content += "<p><i>Không có dữ liệu nhận hàng</i></p>"

        html_content += "<h2>Danh sách sản phẩm đã bán - ĐÃ XUẤT HÓA ĐƠN</h2>"

        if sp_da_xhd:
            html_content += """
            <table>
                <tr>
                    <th>Sản phẩm</th>
                    <th style="text-align: center;">SL</th>
                    <th style="text-align: center;">Loại giá</th>
                    <th style="text-align: right;">Đơn giá</th>
                    <th style="text-align: right;">Thành tiền</th>
                </tr>
            """
            for sp in sp_da_xhd:
                ten, sl, loai_gia, gia, tong = sp
                html_content += f"""
                <tr>
                    <td>{ten}</td>
                    <td style="text-align: center;">{sl:.0f}</td>
                    <td style="text-align: center;">{loai_gia}</td>
                    <td class="money">{gia:,.0f}</td>
                    <td class="money">{tong:,.0f}</td>
                </tr>
                """
            html_content += f"""
                <tr class="total-row">
                    <td colspan="4">TỔNG ĐÃ XUẤT HÓA ĐƠN</td>
                    <td class="money">{tong_tien_xhd:,.0f}</td>
                </tr>
            </table>
            """
        else:
            html_content += "<p><i>Không có sản phẩm đã xuất hóa đơn</i></p>"

        html_content += "<h2>Danh sách sản phẩm đã bán - CHƯA XUẤT HÓA ĐƠN</h2>"

        if sp_chua_xhd:
            html_content += """
            <table>
                <tr>
                    <th>Sản phẩm</th>
                    <th style="text-align: center;">SL</th>
                    <th style="text-align: center;">Loại giá</th>
                    <th style="text-align: right;">Đơn giá</th>
                    <th style="text-align: right;">Thành tiền</th>
                </tr>
            """
            for sp in sp_chua_xhd:
                ten, sl, loai_gia, gia, tong = sp
                html_content += f"""
                <tr>
                    <td>{ten}</td>
                    <td style="text-align: center;">{sl:.0f}</td>
                    <td style="text-align: center;">{loai_gia}</td>
                    <td class="money">{gia:,.0f}</td>
                    <td class="money">{tong:,.0f}</td>
                </tr>
                """
            html_content += f"""
                <tr class="total-row">
                    <td colspan="4">TỔNG CHƯA XUẤT HÓA ĐƠN</td>
                    <td class="money">{tong_tien_chua_xhd:,.0f}</td>
                </tr>
            </table>
            """
        else:
            html_content += "<p><i>Không có sản phẩm chưa xuất hóa đơn</i></p>"

        html_content += f"""
            <h2>Tổng kết tài chính</h2>
                <table>
                    <tr>
                        <th>Khoản mục</th>
                        <th style="text-align: right;">Số tiền</th>
                    </tr>
                    <tr>
                        <td>Tổng tiền bán hàng</td>
                        <td class="money">{tong_tien_ban:,.0f} VNĐ</td>
                    </tr>
                    <tr>
                        <td>Tổng công đoàn</td>
                        <td class="money">{tong_cong_doan:,.0f} VNĐ</td>
                    </tr>
                    <tr>
                        <td>Tổng tiền đã nộp</td>
                        <td class="money">{tong_nop:,.0f} VNĐ</td>
                    </tr>
                    <tr class="total-row">
                        <td>Còn thiếu</td>
                        <td class="money">{tong_thieu:,.0f} VNĐ</td>
                    </tr>
                </table>
            </div>
        </body>
        </html>
        """

        content.setHtml(html_content)
        layout.addWidget(content)

        # Buttons
        btn_layout = QHBoxLayout()

        def do_print():
            # Mở hộp thoại in (cho phép chọn máy in hoặc PDF)
            from PyQt5.QtPrintSupport import QPrintDialog

            printer = QPrinter(QPrinter.HighResolution)
            printer.setPageSize(QPrinter.A4)

            # Mở dialog in
            print_dialog = QPrintDialog(printer, preview_dialog)
            print_dialog.setWindowTitle("In báo cáo đóng ca")

            if print_dialog.exec_() == QPrintDialog.Accepted:
                # In nội dung HTML
                content.document().print_(printer)

                # ✅ Lưu file HTML tổng kết ca vào thư mục riêng và xóa file cũ
                try:
                    _, tong_ket_dir = tao_thu_muc_luu_tru()
                    xoa_file_cu(tong_ket_dir, so_thang=3)  # Xóa file cũ hơn 3 tháng

                    html_filename = f"tong_ket_ca_{self.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                    html_filepath = os.path.join(tong_ket_dir, html_filename)

                    with open(html_filepath, "w", encoding="utf-8") as f:
                        f.write(html_content)

                    print(f"Đã lưu file tổng kết: {html_filename}")
                except Exception as e:
                    print(f"Lỗi khi lưu file tổng kết: {e}")

                show_success(
                    preview_dialog, "Đã in báo cáo đóng ca!"
                )

        def close_shift():
            reply = QMessageBox.question(
                preview_dialog,
                "Xác nhận đóng ca",
                "Bạn có chắc muốn đóng ca không? Tab Bán hàng sẽ bị khóa cho đến khi nhận hàng mới.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                # ✅ Lưu file tổng kết ca khi đóng ca
                try:
                    _, tong_ket_dir = tao_thu_muc_luu_tru()
                    xoa_file_cu(tong_ket_dir, so_thang=3)  # Xóa file cũ hơn 3 tháng

                    html_filename = f"tong_ket_ca_{self.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                    html_filepath = os.path.join(tong_ket_dir, html_filename)

                    with open(html_filepath, "w", encoding="utf-8") as f:
                        f.write(html_content)

                    print(f"Đã lưu file tổng kết: {html_filename}")
                except Exception as e:
                    print(f"Lỗi khi lưu file tổng kết: {e}")

                # Mark shift as closed and disable selling
                self.ca_closed = True
                self.tab_banhang.setEnabled(False)
                # Disable the 'Lưu' button to prevent creating invoices after closing shift
                try:
                    self.btn_luu.setEnabled(False)
                except Exception:
                    pass
                # Reset receive state to allow new receiving
                self.nhan_hang_completed = False
                self.tab_nhan_hang.setEnabled(True)

                # Xóa dữ liệu trong bảng nhận hàng để bắt đầu ca mới
                self.tbl_nhan_hang.setRowCount(0)

                # Close preview
                preview_dialog.accept()
                show_success(
                    self,
                    "Đã đóng ca và lưu báo cáo. Tab Bán hàng bị khóa.\nTab Nhận hàng đã được mở lại và xóa dữ liệu.\nVui lòng ấn 'Tải danh sách sản phẩm' để cập nhật tồn kho mới nhất.",
                )

        btn_print = QPushButton("In báo cáo")
        btn_print.clicked.connect(do_print)
        btn_layout.addWidget(btn_print)

        btn_close = QPushButton("Đóng ca")
        btn_close.clicked.connect(close_shift)
        btn_layout.addWidget(btn_close)

        btn_cancel = QPushButton("Hủy")
        btn_cancel.clicked.connect(preview_dialog.reject)
        btn_layout.addWidget(btn_cancel)

        layout.addLayout(btn_layout)
        preview_dialog.setLayout(layout)
        preview_dialog.exec_()

    def init_tab_nhap_dau_ky(self):
        """Tab nhập đầu kỳ cho số dư user và sản phẩm đã bán chưa xuất hóa đơn"""
        layout = QVBoxLayout()

        # Tạo tab con cho 2 phần: Số dư user và Sản phẩm
        sub_tabs = QTabWidget()

        # === TAB CON 1: NHẬP SỐ DƯ USER ===
        tab_sodu = QWidget()
        layout_sodu = QVBoxLayout()

        layout_sodu.addWidget(QLabel("<b>NHẬP SỐ DƯ ĐẦU KỲ CHO CÁC USER</b>"))

        # Bảng nhập số dư user
        self.tbl_nhap_sodu_user = QTableWidget()
        self.tbl_nhap_sodu_user.setColumnCount(4)
        self.tbl_nhap_sodu_user.setHorizontalHeaderLabels(
            ["ID", "Username", "Số dư hiện tại", "Số dư đầu kỳ"]
        )
        self.setup_table(self.tbl_nhap_sodu_user)
        layout_sodu.addWidget(self.tbl_nhap_sodu_user)

        # Nút tải danh sách user
        btn_load_users = QPushButton("Tải danh sách User")
        btn_load_users.clicked.connect(self.load_nhap_sodu_users)
        layout_sodu.addWidget(btn_load_users)

        # Nút lưu số dư
        btn_save_sodu = QPushButton("Lưu số dư đầu kỳ")
        btn_save_sodu.clicked.connect(self.luu_sodu_dau_ky)
        layout_sodu.addWidget(btn_save_sodu)

        tab_sodu.setLayout(layout_sodu)
        sub_tabs.addTab(tab_sodu, "Số dư User")

        # === TAB CON 2: NHẬP SẢN PHẨM ĐÃ BÁN CHƯA XUẤT HÓA ĐƠN ===
        tab_sanpham = QWidget()
        layout_sp = QVBoxLayout()

        layout_sp.addWidget(
            QLabel("<b>NHẬP ĐẦU KỲ SẢN PHẨM ĐÃ BÁN CHƯA XUẤT HÓA ĐƠN</b>")
        )
        layout_sp.addWidget(QLabel("(Dữ liệu sẽ được chuyển sang tab Xuất bỏ)"))

        # Chọn user
        user_layout = QHBoxLayout()
        user_layout.addWidget(QLabel("Chọn User:"))
        self.combo_user_dau_ky = QComboBox()
        user_layout.addWidget(self.combo_user_dau_ky)
        btn_load_user_combo = QPushButton("Tải danh sách User")
        btn_load_user_combo.clicked.connect(self.load_combo_user_dau_ky)
        user_layout.addWidget(btn_load_user_combo)
        user_layout.addStretch()
        layout_sp.addLayout(user_layout)

        # Bảng nhập sản phẩm - CHỈ 3 CỘT
        self.tbl_nhap_sanpham_dau_ky = QTableWidget()
        self.tbl_nhap_sanpham_dau_ky.setColumnCount(3)
        self.tbl_nhap_sanpham_dau_ky.setHorizontalHeaderLabels(
            ["Tên sản phẩm", "Số lượng", "Loại giá"]
        )
        self.setup_table(self.tbl_nhap_sanpham_dau_ky)

        # Thêm completer cho cột tên sản phẩm
        delegate_sp = CompleterDelegate(self)
        delegate_sp.completer = self.tao_completer_sanpham()
        self.tbl_nhap_sanpham_dau_ky.setItemDelegateForColumn(0, delegate_sp)

        layout_sp.addWidget(self.tbl_nhap_sanpham_dau_ky)

        # Nút thêm dòng
        btn_them_dong_sp = QPushButton("Thêm dòng")
        btn_them_dong_sp.clicked.connect(self.them_dong_nhap_sanpham_dau_ky)
        layout_sp.addWidget(btn_them_dong_sp)

        # Nút lưu sản phẩm đầu kỳ
        btn_save_sp = QPushButton("Lưu sản phẩm đầu kỳ")
        btn_save_sp.clicked.connect(self.luu_sanpham_dau_ky)
        layout_sp.addWidget(btn_save_sp)

        tab_sanpham.setLayout(layout_sp)
        sub_tabs.addTab(tab_sanpham, "Sản phẩm đã bán")

        layout.addWidget(sub_tabs)
        self.tab_nhap_dau_ky.setLayout(layout)

        # Khởi tạo 10 dòng rỗng cho bảng sản phẩm
        for _ in range(10):
            self.them_dong_nhap_sanpham_dau_ky()

    def load_nhap_sodu_users(self):
        """Tải danh sách user để nhập số dư đầu kỳ"""
        from users import lay_tat_ca_user

        users = lay_tat_ca_user()

        self.tbl_nhap_sodu_user.setRowCount(len(users))
        for row, user in enumerate(users):
            # user = (id, username, role, so_du)
            self.tbl_nhap_sodu_user.setItem(row, 0, QTableWidgetItem(str(user[0])))
            self.tbl_nhap_sodu_user.setItem(row, 1, QTableWidgetItem(user[1]))
            so_du_hien_tai = user[3] if len(user) > 3 else 0
            self.tbl_nhap_sodu_user.setItem(
                row, 2, QTableWidgetItem(format_price(so_du_hien_tai))
            )
            # Cột số dư đầu kỳ để trống cho user nhập
            self.tbl_nhap_sodu_user.setItem(row, 3, QTableWidgetItem(""))

        # Ẩn cột ID
        self.tbl_nhap_sodu_user.setColumnHidden(0, True)

    def luu_sodu_dau_ky(self):
        """Lưu số dư đầu kỳ cho các user"""
        from db import ket_noi
        from datetime import datetime

        updates = []
        for row in range(self.tbl_nhap_sodu_user.rowCount()):
            user_id_item = self.tbl_nhap_sodu_user.item(row, 0)
            sodu_dau_ky_item = self.tbl_nhap_sodu_user.item(row, 3)

            if not user_id_item or not sodu_dau_ky_item:
                continue

            sodu_str = sodu_dau_ky_item.text().strip().replace(",", "")
            if not sodu_str:
                continue

            try:
                user_id = int(user_id_item.text())
                so_du_moi = float(sodu_str)
                updates.append((so_du_moi, user_id))
            except ValueError:
                show_error(self, "Lỗi", f"Số dư không hợp lệ ở dòng {row + 1}")
                return

        if not updates:
            show_info(self, "Thông báo", "Không có dữ liệu để cập nhật")
            return

        try:
            conn = ket_noi()
            c = conn.cursor()

            for so_du_moi, user_id in updates:
                # Cập nhật số dư trong bảng Users
                c.execute(
                    "UPDATE Users SET so_du = ? WHERE id = ?", (so_du_moi, user_id)
                )

            conn.commit()

            show_success(self, f"Đã cập nhật số dư cho {len(updates)} user")
            self.load_nhap_sodu_users()
        except Exception as e:
            conn.rollback()
            show_error(self, "Lỗi", f"Lỗi khi lưu số dư: {e}")
        finally:
            conn.close()

    def load_combo_user_dau_ky(self):
        """Tải danh sách user vào combo box"""
        from users import lay_tat_ca_user

        users = lay_tat_ca_user()

        self.combo_user_dau_ky.clear()
        for user in users:
            # user = (id, username, role, so_du)
            self.combo_user_dau_ky.addItem(f"{user[1]} (ID: {user[0]})", user[0])

    def them_dong_nhap_sanpham_dau_ky(self):
        """Thêm dòng rỗng vào bảng nhập sản phẩm đầu kỳ"""
        row = self.tbl_nhap_sanpham_dau_ky.rowCount()
        self.tbl_nhap_sanpham_dau_ky.insertRow(row)

        # Tên sản phẩm
        self.tbl_nhap_sanpham_dau_ky.setItem(row, 0, QTableWidgetItem(""))

        # Số lượng - QDoubleSpinBox
        sl_spin = QDoubleSpinBox()
        # Cho phép 5 chữ số thập phân theo yêu cầu, giữ min âm theo nghiệp vụ đầu kỳ
        sl_spin.setMinimum(-9999)
        sl_spin.setMaximum(9999)
        sl_spin.setDecimals(5)
        sl_spin.setValue(1.0)
        self.tbl_nhap_sanpham_dau_ky.setCellWidget(row, 1, sl_spin)

        # Loại giá - ComboBox
        loai_gia_combo = QComboBox()
        loai_gia_combo.addItems(["le", "buon", "vip"])
        self.tbl_nhap_sanpham_dau_ky.setCellWidget(row, 2, loai_gia_combo)

        # Tổng tiền - CHỈ DÙNG XHD - XÓA HOÀN TOÀN
        # self.tbl_nhap_sanpham_dau_ky.setItem(row, 5, QTableWidgetItem(format_price(0)))

        # XHD checkbox - XÓA
        # xhd_item = QTableWidgetItem()
        # xhd_item.setCheckState(Qt.Unchecked)
        # xhd_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        # self.tbl_nhap_sanpham_dau_ky.setItem(row, 6, xhd_item)

        # Ghi chú - XÓA
        # self.tbl_nhap_sanpham_dau_ky.setItem(row, 7, QTableWidgetItem(""))

    def luu_sanpham_dau_ky(self):
        """Lưu sản phẩm đầu kỳ vào bảng riêng để hiển thị ở tab Xuất bỏ"""
        # Kiểm tra đã chọn user chưa
        if self.combo_user_dau_ky.currentIndex() < 0:
            show_error(self, "Lỗi", "Vui lòng chọn User trước")
            return

        user_id = self.combo_user_dau_ky.currentData()
        if not user_id:
            show_error(self, "Lỗi", "User không hợp lệ")
            return

        # Thu thập dữ liệu từ bảng - CHỈ 3 CỘT
        items = []
        for row in range(self.tbl_nhap_sanpham_dau_ky.rowCount()):
            ten_item = self.tbl_nhap_sanpham_dau_ky.item(row, 0)
            if not ten_item or not ten_item.text().strip():
                continue

            ten = ten_item.text().strip()
            res = tim_sanpham(ten)
            if not res:
                show_error(self, "Lỗi", f"Sản phẩm '{ten}' không tồn tại")
                return

            sanpham_id = res[0][0]
            sp_info = res[
                0
            ]  # [id, ten, gia_le, gia_buon, gia_vip, ton_kho, nguong_buon]

            sl_spin = self.tbl_nhap_sanpham_dau_ky.cellWidget(row, 1)
            so_luong = sl_spin.value() if sl_spin else 0

            loai_gia_combo = self.tbl_nhap_sanpham_dau_ky.cellWidget(row, 2)
            loai_gia = loai_gia_combo.currentText() if loai_gia_combo else "le"

            # Lấy giá tương ứng từ DB
            if loai_gia == "vip":
                gia = float(sp_info[4])
            elif loai_gia == "buon":
                gia = float(sp_info[3])
            else:  # le
                gia = float(sp_info[2])

            items.append(
                {
                    "sanpham_id": sanpham_id,
                    "ten_sanpham": ten,
                    "so_luong": so_luong,
                    "loai_gia": loai_gia,
                    "gia": gia,
                }
            )

        if not items:
            show_error(self, "Lỗi", "Không có sản phẩm nào để lưu")
            return

        # Lưu vào bảng DauKyXuatBo (tạo bảng nếu chưa có)
        from db import ket_noi
        from datetime import datetime

        try:
            conn = ket_noi()
            c = conn.cursor()

            # Tạo bảng DauKyXuatBo nếu chưa có
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
                    FOREIGN KEY (user_id) REFERENCES Users(id),
                    FOREIGN KEY (sanpham_id) REFERENCES SanPham(id)
                )
            """
            )

            ngay = datetime.now().isoformat()

            # Thêm từng sản phẩm vào bảng
            for item in items:
                c.execute(
                    "INSERT INTO DauKyXuatBo (user_id, sanpham_id, ten_sanpham, so_luong, loai_gia, gia, ngay) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        user_id,
                        item["sanpham_id"],
                        item["ten_sanpham"],
                        item["so_luong"],
                        item["loai_gia"],
                        item["gia"],
                        ngay,
                    ),
                )

            conn.commit()
            conn.close()

            show_success(
                self,
                f"Đã lưu {len(items)} sản phẩm đầu kỳ. Dữ liệu sẽ hiển thị ở tab Xuất bỏ.",
            )

            # Xóa dữ liệu bảng
            self.tbl_nhap_sanpham_dau_ky.setRowCount(0)
            for _ in range(10):
                self.them_dong_nhap_sanpham_dau_ky()

            # Làm mới tab Xuất bỏ nếu có
            if hasattr(self, "load_xuatbo"):
                self.load_xuatbo()

        except Exception as e:
            show_error(self, "Lỗi", f"Lỗi khi lưu đầu kỳ: {e}")
            try:
                conn.rollback()
                conn.close()
            except Exception as close_err:
                print(f"Warning: Could not close/rollback connection: {close_err}")


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    # Đảm bảo tạo các bảng DB mới (ví dụ ChenhLech) khi khởi động
    try:
        from db import khoi_tao_db

        khoi_tao_db()
    except Exception:
        pass

    app = QApplication(sys.argv)
    win = DangNhap()
    win.show()
    sys.exit(app.exec_())
