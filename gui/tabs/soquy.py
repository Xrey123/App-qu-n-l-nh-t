from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QDateEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QTabWidget, QDialog, 
    QLineEdit, QSpinBox, QMessageBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QDoubleValidator, QPainter
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog

from db import ket_noi
from utils.money import format_price, MENH_GIA
from utils.ui_helpers import show_error, show_success, setup_quantity_spinbox
from users import lay_tat_ca_user, chuyen_tien
from gui.utils import setup_table

class SoQuyTab(QWidget):
    def __init__(self, user_id, role, main_window=None):
        super().__init__()
        self.user_id = user_id
        self.role = role
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
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
        setup_table(self.tbl_soquy)
        sodu_layout.addWidget(self.tbl_soquy)

        # Nút chuyển tiền (CHỈ cho admin và accountant)
        if self.role in ["admin", "accountant"]:
            btn_layout_quy = QHBoxLayout()
            btn_chuyen_tien = QPushButton("Chuyển tiền")
            btn_chuyen_tien.clicked.connect(self.chuyen_tien_click)
            btn_layout_quy.addWidget(btn_chuyen_tien)
            sodu_layout.addLayout(btn_layout_quy)

        # Tab con: Lịch sử giao dịch
        self.tab_so_quy_ls = QWidget()
        ls_layout = QVBoxLayout()

        # Filter bar: User + Từ ngày + Đến ngày + Tải
        fl = QHBoxLayout()

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
        self.tbl_ls_quy.setHorizontalHeaderLabels(
            ["Thời gian", "Từ user", "Đến user", "Số tiền", "Ca ngày", "Ghi chú"]
        )
        setup_table(self.tbl_ls_quy)
        ls_layout.addWidget(self.tbl_ls_quy)

        self.tab_so_quy_ls.setLayout(ls_layout)
        self.so_quy_tabs.addTab(self.tab_so_quy_ls, "Lịch sử giao dịch")

        self.setLayout(parent_layout)
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
