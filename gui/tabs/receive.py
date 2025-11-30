from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QDoubleSpinBox, QDialog, QHeaderView
)
from PyQt5.QtCore import Qt
from db import ket_noi
from utils.ui_helpers import show_error, show_success, show_info, setup_table
from utils.file_utils import tao_thu_muc_luu_tru, xoa_file_cu
from products import lay_tat_ca_sanpham
import os
import csv
from datetime import datetime

class ReceiveTab(QWidget):
    def __init__(self, user_id, main_window):
        super().__init__()
        self.user_id = user_id
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Kiểm kê / Nhập số lượng hiện có (so sánh với tồn hệ thống):"))

        self.tbl_nhan_hang = QTableWidget()
        self.tbl_nhan_hang.setColumnCount(5)
        self.tbl_nhan_hang.setHorizontalHeaderLabels(
            ["Tên sản phẩm", "Số lượng đếm", "Tồn hệ thống", "Chênh lệch", "Ghi chú"]
        )
        setup_table(self.tbl_nhan_hang)
        layout.addWidget(self.tbl_nhan_hang)

        btn_load_sp = QPushButton("Tải danh sách sản phẩm")
        btn_load_sp.clicked.connect(self.load_sanpham_nhan_hang)
        layout.addWidget(btn_load_sp)

        btn_confirm = QPushButton("Xác nhận nhận hàng")
        btn_confirm.clicked.connect(self.xac_nhan_nhan_hang)
        layout.addWidget(btn_confirm)
        
        self.setLayout(layout)

    def load_sanpham_nhan_hang(self):
        sp_list = lay_tat_ca_sanpham()
        self.tbl_nhan_hang.setRowCount(len(sp_list))
        for row, sp in enumerate(sp_list):
            ten = sp[1]
            ton_db = sp[5] if len(sp) > 5 and sp[5] is not None else 0
            
            self.tbl_nhan_hang.setItem(row, 0, QTableWidgetItem(ten))
            self.tbl_nhan_hang.setItem(row, 1, QTableWidgetItem(str(ton_db))) # Prefill
            self.tbl_nhan_hang.setItem(row, 2, QTableWidgetItem(str(ton_db)))
            self.tbl_nhan_hang.setItem(row, 3, QTableWidgetItem("0"))
            self.tbl_nhan_hang.setItem(row, 4, QTableWidgetItem(""))
            
            # Update main window available products
            if hasattr(self.main_window, 'available_products'):
                self.main_window.available_products[ten] = ton_db

    def xac_nhan_nhan_hang(self):
        nhan_hang_data = []
        discrepancies = []
        
        for row in range(self.tbl_nhan_hang.rowCount()):
            ten_item = self.tbl_nhan_hang.item(row, 0)
            if not ten_item: continue
            
            ten_sp = ten_item.text()
            try:
                sl_dem = float(self.tbl_nhan_hang.item(row, 1).text())
            except ValueError:
                sl_dem = 0
            try:
                ton_db = float(self.tbl_nhan_hang.item(row, 2).text())
            except ValueError:
                ton_db = 0
                
            ghi_chu = self.tbl_nhan_hang.item(row, 4).text() if self.tbl_nhan_hang.item(row, 4) else ""
            chenh = sl_dem - ton_db
            
            self.tbl_nhan_hang.setItem(row, 3, QTableWidgetItem(f"{chenh:g}"))
            
            nhan_hang_data.append((
                self.user_id, ten_sp, sl_dem, ton_db, chenh, ghi_chu, 
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            
            if abs(chenh) >= 1e-9:
                status = "DƯ" if chenh > 0 else "THIẾU"
                discrepancies.append((ten_sp, chenh, status))

        # Save CSV
        try:
            nhan_hang_dir, _ = tao_thu_muc_luu_tru()
            xoa_file_cu(nhan_hang_dir, so_thang=3)
            filename = f"nhan_hang_{self.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join(nhan_hang_dir, filename)
            
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["user_id", "ten_sp", "so_luong_dem", "ton_db", "chenh_lech", "ghi_chu", "thoi_gian"])
                writer.writerows(nhan_hang_data)
        except Exception as e:
            print(f"Warning: Could not save CSV: {e}")

        if discrepancies:
            self.show_discrepancy_dialog(discrepancies, nhan_hang_data)
        else:
            self.finish_receiving(nhan_hang_data)
            show_info(self, "Kiểm kê", "Không có chênh lệch. Đã lưu kết quả kiểm kê.")

    def show_discrepancy_dialog(self, discrepancies, nhan_hang_data):
        dlg = QDialog(self)
        dlg.setWindowTitle("Xác nhận chênh lệch kho")
        dlg.resize(800, 400)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Phát hiện chênh lệch ({len(discrepancies)} sản phẩm). Chọn mục để áp vào kho."))
        
        tbl = QTableWidget()
        tbl.setColumnCount(5)
        tbl.setHorizontalHeaderLabels(["Chọn", "Sản phẩm", "Tồn hệ thống", "Chênh lệch", "Lý do (bắt buộc)"])
        tbl.setRowCount(len(discrepancies))
        
        for i, (ten, chenh, status) in enumerate(discrepancies):
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chk.setCheckState(Qt.Checked)
            tbl.setItem(i, 0, chk)
            tbl.setItem(i, 1, QTableWidgetItem(ten))
            
            ton_db = next((r[3] for r in nhan_hang_data if r[1] == ten), 0)
            tbl.setItem(i, 2, QTableWidgetItem(str(ton_db)))
            tbl.setItem(i, 3, QTableWidgetItem(f"{chenh:g}"))
            tbl.setItem(i, 4, QTableWidgetItem(""))
            
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(tbl)
        
        btns = QHBoxLayout()
        apply_btn = QPushButton("Áp chênh lệch")
        cancel_btn = QPushButton("Hủy")
        btns.addWidget(apply_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)
        dlg.setLayout(layout)
        
        apply_btn.clicked.connect(lambda: self.apply_discrepancies(dlg, tbl, nhan_hang_data))
        cancel_btn.clicked.connect(dlg.reject)
        
        if dlg.exec_() != QDialog.Accepted:
            show_info(self, "Hủy", "Bạn đã hủy nhận hàng.")
        else:
            self.finish_receiving(nhan_hang_data)

    def apply_discrepancies(self, dlg, tbl, nhan_hang_data):
        to_apply = []
        for r in range(tbl.rowCount()):
            if tbl.item(r, 0).checkState() == Qt.Checked:
                ten = tbl.item(r, 1).text()
                chenh = float(tbl.item(r, 3).text())
                reason = tbl.item(r, 4).text().strip()
                if not reason:
                    show_error(dlg, "Lỗi", f"Thiếu lý do cho {ten}")
                    return
                to_apply.append((ten, chenh, reason))
        
        if not to_apply:
            show_info(dlg, "Thông báo", "Chưa chọn mục nào")
            return

        conn = ket_noi()
        c = conn.cursor()
        try:
            for ten, ch, reason in to_apply:
                c.execute("SELECT id, ton_kho FROM SanPham WHERE ten=?", (ten,))
                row = c.fetchone()
                if not row: continue
                sp_id, ton_truoc = row
                
                counted = next((r[2] for r in nhan_hang_data if r[1] == ten), ton_truoc + ch)
                ton_sau = counted
                
                c.execute("UPDATE SanPham SET ton_kho=? WHERE id=?", (ton_sau, sp_id))
                
                ngay = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("""
                    INSERT INTO LogKho (sanpham_id, user_id, ngay, hanh_dong, so_luong, ton_truoc, ton_sau, gia_ap_dung, chenh_lech_cong_doan) 
                    VALUES (?, ?, ?, 'kiemke', ?, ?, ?, 0, ?)
                """, (sp_id, self.user_id, ngay, ch, ton_truoc, ton_sau, ch))
                
                c.execute("""
                    INSERT INTO ChenhLech (sanpham_id, user_id, ngay, chenh, ton_truoc, ton_sau, ghi_chu)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (sp_id, self.user_id, ngay, ch, ton_truoc, ton_sau, reason))
                
            conn.commit()
            
            # Update in-memory for applied items
            for ten, ch, _ in to_apply:
                counted = next((r[2] for r in nhan_hang_data if r[1] == ten), 0)
                if hasattr(self.main_window, 'available_products'):
                    self.main_window.available_products[ten] = counted
            
            dlg.accept()
            show_success(self, "Đã áp chênh lệch thành công")
            
        except Exception as e:
            conn.rollback()
            show_error(dlg, "Lỗi", f"Lỗi DB: {e}")
        finally:
            conn.close()

    def finish_receiving(self, nhan_hang_data):
        # Update all available products based on count
        if hasattr(self.main_window, 'available_products'):
            for rec in nhan_hang_data:
                ten = rec[1]
                qty = rec[2]
                self.main_window.available_products[ten] = qty
        
        if hasattr(self.main_window, 'cap_nhat_completer_sanpham'):
            self.main_window.cap_nhat_completer_sanpham()
        
        # ✅ SET FLAG: Đã hoàn thành nhận hàng
        if hasattr(self.main_window, 'nhan_hang_completed'):
            self.main_window.nhan_hang_completed = True
            
        self.setEnabled(False)
        if hasattr(self.main_window, 'tab_banhang'):
            self.main_window.tab_banhang.setEnabled(True)
            if hasattr(self.main_window.tab_banhang, 'btn_luu'):
                self.main_window.tab_banhang.btn_luu.setEnabled(True)
        
        show_success(self, "Nhận hàng thành công. Đã mở khóa bán hàng.")
