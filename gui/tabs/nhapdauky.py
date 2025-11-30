from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, 
    QTableWidget, QTableWidgetItem, QTabWidget, QDoubleSpinBox, QStyledItemDelegate, QLineEdit
)
from PyQt5.QtCore import Qt
from gui.utils import setup_table
from db import ket_noi
from utils.money import format_price
from utils.ui_helpers import show_error, show_success, show_info
from users import lay_tat_ca_user
from products import tim_sanpham
from datetime import datetime

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

class NhapDauKyTab(QWidget):
    def __init__(self, user_id, main_window):
        super().__init__()
        self.user_id = user_id
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
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
        self.tbl_nhap_sodu_user.setHorizontalHeaderLabels(
            ["ID", "Username", "Số dư hiện tại", "Số dư đầu kỳ"]
        )
        setup_table(self.tbl_nhap_sodu_user)
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
        self.tbl_nhap_sanpham_dau_ky.setHorizontalHeaderLabels(
            ["Tên sản phẩm", "Số lượng", "Loại giá"]
        )
        setup_table(self.tbl_nhap_sanpham_dau_ky)

        # Thêm completer cho cột tên sản phẩm
        delegate_sp = CompleterDelegate(self)
        # Reuse completer from main window if available
        if hasattr(self.main_window, 'tao_completer_sanpham'):
            delegate_sp.completer = self.main_window.tao_completer_sanpham()
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
        self.setLayout(layout)

        # Khởi tạo 10 dòng rỗng cho bảng sản phẩm
        for _ in range(10):
            self.them_dong_nhap_sanpham_dau_ky()



    def load_nhap_sodu_users(self):
        """Tải danh sách user để nhập số dư đầu kỳ"""
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
            if hasattr(self.main_window, "tab_xuat_bo") and hasattr(self.main_window.tab_xuat_bo, "load_xuatbo"):
                 # Assuming tab_xuat_bo is the widget, but it might be the wrapper. 
                 # In main_window.py: self.tab_xuat_bo = XuatBoTab(...)
                 # So we can call self.main_window.tab_xuat_bo.load_xuatbo()
                 self.main_window.tab_xuat_bo.load_xuatbo()

        except Exception as e:
            show_error(self, "Lỗi", f"Lỗi khi lưu đầu kỳ: {e}")
            try:
                conn.rollback()
                conn.close()
            except Exception as close_err:
                print(f"Warning: Could not close/rollback connection: {close_err}")
