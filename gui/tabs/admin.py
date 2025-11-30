from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QInputDialog, QLineEdit
)
from gui.utils import setup_table, format_price
from utils.ui_helpers import show_error, show_success
from users import lay_tat_ca_user, them_user, xoa_user

class AdminTab(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.tbl_user = QTableWidget()
        self.tbl_user.setColumnCount(4)
        self.tbl_user.setHorizontalHeaderLabels(["ID", "Username", "Role", "Số dư"])
        setup_table(self.tbl_user)
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
        self.setLayout(layout)

    def them_user_click(self):
        username, ok = QInputDialog.getText(self, "Thêm user", "Username:")
        if not ok: return
        password, ok = QInputDialog.getText(self, "Thêm user", "Password:", QLineEdit.Password)
        if not ok: return
        role, ok = QInputDialog.getItem(self, "Thêm user", "Role:", ["admin", "accountant", "staff"], 0)
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
