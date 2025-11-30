from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QTabWidget, QComboBox
)
from PyQt5.QtCore import Qt, QDate
from gui.utils import setup_table, format_price
from utils.ui_helpers import show_error
from db import ket_noi
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import pandas as pd

class ReportTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        tab_widget = QTabWidget()

        # Tab 1: Inventory Report
        tab_kho = QWidget()
        kho_layout = QVBoxLayout()
        
        btn_kho = QPushButton("Làm mới báo cáo kho")
        btn_kho.clicked.connect(self.xem_bao_cao_kho)
        kho_layout.addWidget(btn_kho)

        self.tbl_baocao_kho = QTableWidget()
        self.tbl_baocao_kho.setColumnCount(7)
        self.tbl_baocao_kho.setHorizontalHeaderLabels(
            ["Tên sản phẩm", "Tồn kho", "Số lượng XHĐ", "Số lượng xuất bổ", "Số lượng chưa xuất", "SYS", "Trạng thái"]
        )
        setup_table(self.tbl_baocao_kho)
        kho_layout.addWidget(self.tbl_baocao_kho)
        
        tab_kho.setLayout(kho_layout)
        tab_widget.addTab(tab_kho, "Báo cáo kho")

        # Tab 2: Chart
        tab_bieudo = QWidget()
        bieudo_layout = QVBoxLayout()
        
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Năm:"))
        self.bieudo_year = QComboBox()
        current_year = QDate.currentDate().year()
        self.bieudo_year.addItems([str(year) for year in range(current_year - 5, current_year + 1)])
        self.bieudo_year.setCurrentText(str(current_year))
        filter_layout.addWidget(self.bieudo_year)

        filter_layout.addWidget(QLabel("Tháng:"))
        self.bieudo_month = QComboBox()
        self.bieudo_month.addItems(["Tất cả"] + [str(m) for m in range(1, 13)])
        filter_layout.addWidget(self.bieudo_month)

        btn_update = QPushButton("Cập nhật biểu đồ")
        btn_update.clicked.connect(self.cap_nhat_bieu_do)
        filter_layout.addWidget(btn_update)
        filter_layout.addStretch()
        
        bieudo_layout.addLayout(filter_layout)

        self.figure = Figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        bieudo_layout.addWidget(self.canvas)
        
        tab_bieudo.setLayout(bieudo_layout)
        tab_widget.addTab(tab_bieudo, "Biểu đồ sản lượng")

        layout.addWidget(tab_widget)
        self.setLayout(layout)

    def xem_bao_cao_kho(self):
        try:
            conn = ket_noi()
            c = conn.cursor()
            
            # Get all products with nguong_buon
            c.execute("SELECT id, ten, ton_kho, nguong_buon FROM SanPham ORDER BY ten")
            products = c.fetchall()
            
            report_data = []
            
            for p in products:
                p_id, ten, ton_kho, nguong_buon = p
                
                # Calculate XHD (Total Sold via Invoice)
                c.execute("""
                    SELECT COALESCE(SUM(so_luong), 0) FROM ChiTietHoaDon 
                    WHERE sanpham_id = ? AND xuat_hoa_don = 1
                """, (p_id,))
                xhd = c.fetchone()[0]
                
                # Calculate Xuat Bo (Total Supplementary Export)
                c.execute("""
                    SELECT COALESCE(SUM(so_luong), 0) FROM ChenhLechXuatBo 
                    WHERE ten_sanpham = ?
                """, (ten,))
                xuat_bo = c.fetchone()[0]
                
                # Calculate Chua Xuat (Sold but not Invoiced yet)  
                # Chua Xuat = (Total Sold in CTHD where xuat_hoa_don=0) + (DauKyXuatBo)
                
                c.execute("""
                    SELECT COALESCE(SUM(so_luong), 0) FROM ChiTietHoaDon 
                    WHERE sanpham_id = ? AND xuat_hoa_don = 0
                """, (p_id,))
                chua_xuat_cthd = c.fetchone()[0]
                
                c.execute("""
                    SELECT COALESCE(SUM(so_luong), 0) FROM DauKyXuatBo 
                    WHERE ten_sanpham = ?
                """, (ten,))
                dau_ky = c.fetchone()[0]
                
                chua_xuat = chua_xuat_cthd + dau_ky
                
                # SYS = Ton kho + Chua Xuat
                sys_val = ton_kho + chua_xuat
                
                # Logic trạng thái - MATCH VỚI MAIN_GUI.PY
                trang_thai = ""
                if ton_kho is None:
                    ton_kho = 0
                if nguong_buon is None:
                    nguong_buon = 0
                if ton_kho < nguong_buon:
                    trang_thai = "Dưới ngưỡng buôn"
                
                report_data.append({
                    "ten": ten,
                    "ton_kho": ton_kho,
                    "xhd": xhd,
                    "xuat_bo": xuat_bo,
                    "chua_xuat": chua_xuat,
                    "sys": sys_val,
                    "status": trang_thai
                })
            
            conn.close()
            
            self.tbl_baocao_kho.setRowCount(len(report_data))
            for row, item in enumerate(report_data):
                self.tbl_baocao_kho.setItem(row, 0, QTableWidgetItem(item["ten"]))
                self.tbl_baocao_kho.setItem(row, 1, QTableWidgetItem(str(item["ton_kho"])))
                self.tbl_baocao_kho.setItem(row, 2, QTableWidgetItem(str(item["xhd"])))
                self.tbl_baocao_kho.setItem(row, 3, QTableWidgetItem(str(item["xuat_bo"])))
                self.tbl_baocao_kho.setItem(row, 4, QTableWidgetItem(str(item["chua_xuat"])))
                self.tbl_baocao_kho.setItem(row, 5, QTableWidgetItem(str(item["sys"])))
                self.tbl_baocao_kho.setItem(row, 6, QTableWidgetItem(item["status"]))
                
        except Exception as e:
            show_error(self, "Lỗi", f"Không thể tải báo cáo kho: {e}")

    def cap_nhat_bieu_do(self):
        year = self.bieudo_year.currentText()
        month = self.bieudo_month.currentText()
        
        try:
            conn = ket_noi()
            query = """
                SELECT s.ten, SUM(ct.so_luong) as tong_sl
                FROM ChiTietHoaDon ct
                JOIN HoaDon h ON ct.hoadon_id = h.id
                JOIN SanPham s ON ct.sanpham_id = s.id
                WHERE strftime('%Y', h.ngay) = ?
            """
            params = [year]
            
            if month != "Tất cả":
                query += " AND strftime('%m', h.ngay) = ?"
                params.append(f"{int(month):02d}")
                
            query += " GROUP BY s.ten ORDER BY tong_sl DESC LIMIT 10"
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            if not df.empty:
                ax.bar(df['ten'], df['tong_sl'])
                ax.set_title(f"Top 10 Sản phẩm bán chạy ({month}/{year})")
                ax.set_xlabel("Sản phẩm")
                ax.set_ylabel("Số lượng")
                plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
            else:
                ax.text(0.5, 0.5, "Không có dữ liệu", ha='center', va='center')
                
            self.figure.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            show_error(self, "Lỗi", f"Lỗi vẽ biểu đồ: {e}")
