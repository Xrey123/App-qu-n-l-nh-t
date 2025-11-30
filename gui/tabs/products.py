from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QLabel, QDateEdit, QTreeWidget, QTreeWidgetItem,
    QHeaderView, QMessageBox, QInputDialog
)
from PyQt5.QtCore import Qt, QDate
from gui.utils import setup_table, format_price
from utils.ui_helpers import show_error, show_info, show_confirmation
from db import ket_noi
from products import (
    lay_tat_ca_sanpham, them_sanpham, xoa_sanpham, 
    import_sanpham_from_dataframe, cap_nhat_ton
)
import pandas as pd
from collections import defaultdict

class ProductTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.tbl_sanpham = QTableWidget()
        self.tbl_sanpham.setColumnCount(7)
        self.tbl_sanpham.setHorizontalHeaderLabels(
            ["ID", "Tên", "Giá lẻ", "Giá buôn", "Giá VIP", "Tồn kho", "Ngưỡng buôn"]
        )
        setup_table(self.tbl_sanpham)

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
        self.setLayout(layout)

    def load_sanpham(self):
        try:
            products = lay_tat_ca_sanpham()
            self.tbl_sanpham.setRowCount(len(products))
            self.tbl_sanpham.blockSignals(True)  # Block signals to prevent update loop
            
            for row, prod in enumerate(products):
                # ID, Ten, Gia Le, Gia Buon, Gia VIP, Ton Kho, Nguong Buon
                for col, val in enumerate(prod):
                    item = QTableWidgetItem(str(val))
                    # ID and Name read-only
                    if col in [0, 1]:
                        item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                    self.tbl_sanpham.setItem(row, col, item)
            
            self.tbl_sanpham.blockSignals(False)
        except Exception as e:
            show_error(self, "Lỗi", f"Không thể tải danh sách sản phẩm: {e}")

    def update_product_price(self, item):
        row = item.row()
        col = item.column()
        
        # Only handle price/stock columns (2-6)
        if col not in [2, 3, 4, 5, 6]:
            return

        try:
            new_value = float(item.text())
            prod_id = int(self.tbl_sanpham.item(row, 0).text())
            
            conn = ket_noi()
            c = conn.cursor()
            
            if col == 2: # Gia le
                c.execute("UPDATE SanPham SET gia_le=? WHERE id=?", (new_value, prod_id))
            elif col == 3: # Gia buon
                c.execute("UPDATE SanPham SET gia_buon=? WHERE id=?", (new_value, prod_id))
            elif col == 4: # Gia vip
                c.execute("UPDATE SanPham SET gia_vip=? WHERE id=?", (new_value, prod_id))
            elif col == 5: # Ton kho
                c.execute("UPDATE SanPham SET ton_kho=? WHERE id=?", (new_value, prod_id))
            elif col == 6: # Nguong buon
                c.execute("UPDATE SanPham SET nguong_buon=? WHERE id=?", (new_value, prod_id))
                
            conn.commit()
            conn.close()
            
            # Log history if needed (simplified for now)
            
        except ValueError:
            show_error(self, "Lỗi", "Vui lòng nhập số hợp lệ")
            self.load_sanpham() # Reload to reset invalid value
        except Exception as e:
            show_error(self, "Lỗi", f"Lỗi cập nhật: {e}")

    def them_sanpham_click(self):
        # Simplified dialog implementation
        ten, ok = QInputDialog.getText(self, "Thêm sản phẩm", "Tên sản phẩm:")
        if ok and ten:
            if them_sanpham(ten, 0, 0, 0):
                self.load_sanpham()
                show_info(self, "Thành công", "Đã thêm sản phẩm mới")
            else:
                show_error(self, "Lỗi", "Thêm sản phẩm thất bại")

    def nhap_kho_click(self):
        # Implementation for quick stock entry
        row = self.tbl_sanpham.currentRow()
        if row < 0:
            show_error(self, "Lỗi", "Vui lòng chọn sản phẩm cần nhập kho")
            return
            
        prod_id = int(self.tbl_sanpham.item(row, 0).text())
        ten = self.tbl_sanpham.item(row, 1).text()
        current_stock = float(self.tbl_sanpham.item(row, 5).text())
        
        qty, ok = QInputDialog.getDouble(self, "Nhập kho", f"Nhập thêm số lượng cho '{ten}':", 0, 0, 10000, 2)
        if ok and qty > 0:
            if cap_nhat_ton(prod_id, current_stock + qty):
                self.load_sanpham()
                show_info(self, "Thành công", f"Đã nhập thêm {qty} cho {ten}")

    def xoa_sanpham_click(self):
        row = self.tbl_sanpham.currentRow()
        if row < 0:
            show_error(self, "Lỗi", "Vui lòng chọn sản phẩm cần xóa")
            return
            
        ten = self.tbl_sanpham.item(row, 1).text()
        if show_confirmation(self, "Xác nhận", f"Bạn có chắc muốn xóa sản phẩm '{ten}'?"):
            if xoa_sanpham(ten):
                self.load_sanpham()
                show_info(self, "Thành công", "Đã xóa sản phẩm")

    def import_sanpham_excel(self):
        from PyQt5.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn file Excel", "", "Excel Files (*.xlsx *.xls)")
        if file_path:
            try:
                df = pd.read_excel(file_path)
                if import_sanpham_from_dataframe(df):
                    self.load_sanpham()
                    show_info(self, "Thành công", "Import dữ liệu thành công")
                else:
                    show_error(self, "Lỗi", "Import thất bại")
            except Exception as e:
                show_error(self, "Lỗi", f"Lỗi đọc file: {e}")

class PriceHistoryTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Tab để xem lịch sử thay đổi giá - hiển thị theo ngày với 3 loại giá"""
        layout = QVBoxLayout()

        # Hướng dẫn sử dụng
        info_label = QLabel(
            "💡 Cách thay đổi giá:\n"
            "1. Tab Sản phẩm: Double-click vào ô giá để sửa từng sản phẩm\n"
            "2. Tab Sản phẩm: Nhấn 'Import Excel' để cập nhật giá hàng loạt"
        )
        info_label.setStyleSheet(
            "background-color: #fff3cd; padding: 10px; border-radius: 5px;"
        )
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
        self.tree_lich_su_gia = QTreeWidget()
        self.tree_lich_su_gia.setHeaderLabels(
            [
                "Ngày/Sản phẩm",
                "Lẻ cũ",
                "Lẻ mới",
                "Buôn cũ",
                "Buôn mới",
                "VIP cũ",
                "VIP mới",
                "User",
            ]
        )
        self.tree_lich_su_gia.setAlternatingRowColors(True)
        layout.addWidget(self.tree_lich_su_gia)

        # Label tổng số thay đổi
        self.lbl_tong_lich_su = QLabel("Tổng số sản phẩm: 0")
        layout.addWidget(self.lbl_tong_lich_su)

        self.setLayout(layout)
        self.load_lich_su_gia()

    def load_lich_su_gia(self):
        """Load dữ liệu lịch sử thay đổi giá - hiển thị TẤT CẢ sản phẩm"""
        try:
            conn = ket_noi()
            c = conn.cursor()

            tu_ngay = self.lich_su_gia_tu.date().toString("yyyy-MM-dd")
            den_ngay = self.lich_su_gia_den.date().toString("yyyy-MM-dd")

            # 1. Lấy TẤT CẢ sản phẩm hiện có
            c.execute(
                "SELECT id, ten, gia_le, gia_buon, gia_vip FROM SanPham ORDER BY ten"
            )
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
                    "gia_cu": gia_cu,
                    "gia_moi": gia_moi,
                    "username": username,
                }

            # 4. Tạo dict để tra cứu giá hiện tại
            current_prices = {}
            for sp_id, ten, gia_le, gia_buon, gia_vip in all_products:
                current_prices[ten] = {"le": gia_le, "buon": gia_buon, "vip": gia_vip}

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
                        if "le" in data:
                            child.setText(1, format_price(data["le"]["gia_cu"]))
                            child.setText(2, format_price(data["le"]["gia_moi"]))
                        elif ten_sp in current_prices:
                            # Chưa thay đổi giá lẻ → hiển thị giá hiện tại
                            gia = current_prices[ten_sp]["le"]
                            child.setText(1, format_price(gia))
                            child.setText(2, format_price(gia))

                        # Buôn
                        if "buon" in data:
                            child.setText(3, format_price(data["buon"]["gia_cu"]))
                            child.setText(4, format_price(data["buon"]["gia_moi"]))
                        elif ten_sp in current_prices:
                            gia = current_prices[ten_sp]["buon"]
                            child.setText(3, format_price(gia))
                            child.setText(4, format_price(gia))

                        # VIP
                        if "vip" in data:
                            child.setText(5, format_price(data["vip"]["gia_cu"]))
                            child.setText(6, format_price(data["vip"]["gia_moi"]))
                        elif ten_sp in current_prices:
                            gia = current_prices[ten_sp]["vip"]
                            child.setText(5, format_price(gia))
                            child.setText(6, format_price(gia))

                        # User
                        username = ""
                        for loai in ["le", "buon", "vip"]:
                            if loai in data:
                                username = data[loai]["username"] or ""
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
