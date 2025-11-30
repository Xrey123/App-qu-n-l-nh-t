"""
Tab Chênh lệch - Quản lý chênh lệch kho từ bảng ChenhLech
Migrated from main_gui.py (dòng 2165-2383)
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QDateEdit, QDialog,
    QComboBox, QLineEdit, QMessageBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QDoubleValidator
from datetime import datetime

from db import ket_noi
from users import lay_tat_ca_user, chuyen_tien
from products import tim_sanpham
from utils.ui_helpers import show_error, show_success, setup_table


class ChenhLechTab(QWidget):
    def __init__(self, user_id, role, main_window):
        super().__init__()
        self.user_id = user_id
        self.role = role
        self.main_window = main_window
        self.init_ui()
    
    def init_ui(self):
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
        setup_table(self.tbl_chenhlech)
        layout.addWidget(self.tbl_chenhlech)
        
        # Thêm nút xử lý chênh lệch (góc phải)
        btn_layout_chenh = QHBoxLayout()
        btn_layout_chenh.addStretch()
        btn_xu_ly_chenh = QPushButton("Xử lý chênh lệch")
        btn_xu_ly_chenh.clicked.connect(self.xu_ly_chenh_lech_click)
        btn_layout_chenh.addWidget(btn_xu_ly_chenh)
        layout.addLayout(btn_layout_chenh)
        
        self.setLayout(layout)
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
                sp = tim_sanpham(ten_sp)
                if not sp:
                    continue
                sp = sp[0]
                gia_le = sp[2]
                
                if xu_ly_type == 0:  # Bán bổ sung (nộp tiền)
                    # Cộng tiền vào số dư user
                    so_tien = abs(chenh) * gia_le
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
            show_success(self, "Đã xử lý chênh lệch thành công")
            self.load_chenhlech()  # Reload
        except Exception as e:
            conn.rollback()
            show_error(self, "Lỗi", f"Lỗi xử lý: {e}")
        finally:
            conn.close()
