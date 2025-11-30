"""
MainWindow - Cửa sổ chính của ứng dụng
Sử dụng các module đã được tách riêng từ gui/tabs/
"""
from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QMessageBox, QApplication,
    QToolBar, QLabel, QPushButton, QDialog, QLineEdit, QHBoxLayout, QSizePolicy
)
from PyQt5.QtCore import Qt, QSize
import logging

from gui.tabs.home import HomeTab
from gui.tabs.products import ProductTab, PriceHistoryTab
from gui.tabs.sales import SalesTab
from gui.tabs.receive import ReceiveTab
from gui.tabs.invoices import InvoiceTab
from gui.tabs.reports import ReportTab
from gui.tabs.admin import AdminTab  
from gui.tabs.settings import SettingsTab
from gui.tabs.others import XuatBoTab
from gui.tabs.chenhlech import ChenhLechTab
from gui.tabs.chitietban import ChiTietBanTab
from gui.tabs.congdoan import CongDoanTab
from gui.tabs.soquy import SoQuyTab
from gui.tabs.nhapdauky import NhapDauKyTab
from products import lay_tat_ca_sanpham

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self, user_id, role, login_window):
        super().__init__()
        self.user_id = user_id
        self.role = role
        self.login_window = login_window
        
        # Shared state
        self.available_products = {}  # {product_name: quantity}
        self.nhan_hang_completed = False
        self.ca_closed = False
        self.last_invoice_id = None
        
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Shop Flow")  # Chỉ hiện tên app, không hiện role
        self.setGeometry(100, 100, 1400, 900)
        
        # Set window icon if available
        try:
            from PyQt5.QtGui import QIcon
            # You can add icon file here: self.setWindowIcon(QIcon('path/to/icon.png'))
        except:
            pass
        
        # === TOOLBAR: CHANGE PASSWORD & LOGOUT ===
        from db import ket_noi
        
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(16, 16))
        toolbar.setStyleSheet("""
            QToolBar {
                background: #f5f5f5;
                border-bottom: 1px solid #ddd;
                spacing: 10px;
                padding: 5px;
            }
        """)
        self.addToolBar(toolbar)
        
        # === LOGO & TITLE ===
        try:
            from PyQt5.QtGui import QIcon
            # Set window icon
            self.setWindowIcon(QIcon('logo.png'))
            
        except Exception as e:
            logger.error(f"Error setting logo: {e}")
        
        
        # Spacer to push buttons to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)
        
        # User info label
        try:
            conn = ket_noi()
            c = conn.cursor()
            c.execute("SELECT username FROM Users WHERE id=?", (self.user_id,))
            row = c.fetchone()
            username = row[0] if row else "User"
            conn.close()
        except:
            username = "User"
        
        user_label = QLabel(f"👤 {username} ({self.role})")
        user_label.setStyleSheet("color: #333; font-weight: bold; margin-right: 15px;")
        toolbar.addWidget(user_label)
        
        # Change password button (no icon, font 9px)
        btn_change_pass = QPushButton("Đổi mật khẩu")
        btn_change_pass.setFlat(True)
        btn_change_pass.setCursor(Qt.PointingHandCursor)
        btn_change_pass.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                color: #0066cc;
                font-size: 15px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                color: #ff6600;
                background: #e8f4ff;
                border-radius: 3px;
            }
        """)
        btn_change_pass.clicked.connect(self.doi_mat_khau)
        toolbar.addWidget(btn_change_pass)
        
        # Logout button (no icon, font 9px)
        btn_logout = QPushButton("Đăng xuất")
        btn_logout.setFlat(True)
        btn_logout.setCursor(Qt.PointingHandCursor)
        btn_logout.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                color: #cc0000;
                font-size: 15px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                color: #ff3333;
                background: #ffe8e8;
                border-radius: 3px;
            }
        """)
        btn_logout.clicked.connect(self.dang_xuat)
        toolbar.addWidget(btn_logout)
        
        # === MAIN TABS ===
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Tab Trang chủ (FIRST - always visible)
        self.tab_home = HomeTab()
        self.tabs.addTab(self.tab_home, "Trang chủ")
        
        # Tab Nhận hàng (initially enabled)
        self.tab_nhan_hang = ReceiveTab(self.user_id, self)
        self.tabs.addTab(self.tab_nhan_hang, "Nhận hàng")
        
        # Tab Bán hàng (initially disabled until receiving is done)
        self.tab_banhang = SalesTab(self.user_id, self)
        self.tabs.addTab(self.tab_banhang, "Bán hàng")
        self.tab_banhang.setEnabled(False)
        
        # Tab Chi tiết bán (xem các ca bán hàng)
        self.tab_chitietban = ChiTietBanTab(self.user_id, self.role, self)
        self.tabs.addTab(self.tab_chitietban, "Chi tiết bán")
        
        # Tab Hóa đơn
        self.tab_hoadon = InvoiceTab(self.user_id, self.role)
        self.tabs.addTab(self.tab_hoadon, "Hóa đơn")
        
        # Tab Báo cáo
        self.tab_baocao = ReportTab(self)
        self.tabs.addTab(self.tab_baocao, "Báo cáo")
        
        # Tab Sản phẩm và Lịch sử giá (ONLY for admin and accountant)
        if self.role in ["admin", "accountant"]:
            self.tab_sanpham = ProductTab()
            self.tabs.addTab(self.tab_sanpham, "Sản phẩm")
            
            self.tab_lich_su_gia = PriceHistoryTab()
            self.tabs.addTab(self.tab_lich_su_gia, "Lịch sử giá")
        
        # Tab Xuất bổ (if accountant or admin)
        if self.role in ["admin", "accountant"]:
            self.tab_xuat_bo = XuatBoTab(self.user_id, self)  # Pass self for completer access
            self.tabs.addTab(self.tab_xuat_bo, "Xuất bổ")
            
            # Tab Chênh lệch (cho admin và accountant)
            self.tab_chenhlech = ChenhLechTab(self.user_id, self.role, self)
            self.tabs.addTab(self.tab_chenhlech, "Chênh lệch")
        
        # Tabs for accountant: Công đoàn, Sổ quỹ, Nhập đầu kỳ
        if self.role in ["admin", "accountant"]:
            self.tab_cong_doan = CongDoanTab(self.user_id, self)
            self.tabs.addTab(self.tab_cong_doan, "Công đoàn")
            
            self.tab_so_quy = SoQuyTab(self.user_id, self.role)
            self.tabs.addTab(self.tab_so_quy, "Sổ quỹ")
            
            self.tab_nhap_dau_ky = NhapDauKyTab(self.user_id, self)
            self.tabs.addTab(self.tab_nhap_dau_ky, "Nhập đầu kỳ")
        else:
            # Staff can view Sổ quỹ but with limited permissions
            self.tab_so_quy = SoQuyTab(self.user_id, self.role)
            self.tabs.addTab(self.tab_so_quy, "Sổ quỹ")
        
        # Tab Admin (only for admin)
        if self.role == "admin":
            self.tab_user = AdminTab(self.user_id)
            self.tabs.addTab(self.tab_user, "Quản lý Users")
            
            # Tab Settings (only for admin)
            self.tab_settings = SettingsTab()
            self.tabs.addTab(self.tab_settings, "⚙️ Cài đặt")
        
        self.show()
    
    def tao_completer_sanpham(self):
        """Tạo QCompleter cho tên sản phẩm"""
        from PyQt5.QtWidgets import QCompleter
        from PyQt5.QtCore import Qt
        
        try:
            products = lay_tat_ca_sanpham()
            names = [p[1] for p in products]  # p[1] is product name
            
            completer = QCompleter(names)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setFilterMode(Qt.MatchContains)
            return completer
        except Exception as e:
            logger.error(f"Error creating completer: {e}")
            return QCompleter([])
    
    def cap_nhat_completer_sanpham(self):
        """Cập nhật lại completer sau khi thêm/xóa sản phẩm"""
        pass
    
    def refresh_all_tabs(self):
        """Refresh tất cả các tab để cập nhật dữ liệu mới"""
        try:
            # Refresh Chi tiết bán
            if hasattr(self, 'tab_chitietban') and hasattr(self.tab_chitietban, 'load_chitietban'):
                self.tab_chitietban.load_chitietban()
            
            # Refresh Sổ quỹ
            if hasattr(self, 'tab_so_quy') and hasattr(self.tab_so_quy, 'load_soquy'):
                self.tab_so_quy.load_soquy()
            
            # Refresh Công đoàn
            if hasattr(self, 'tab_cong_doan') and hasattr(self.tab_cong_doan, 'load_cong_doan'):
                self.tab_cong_doan.load_cong_doan()
            
            # Refresh Báo cáo
            if hasattr(self, 'tab_baocao'):
                # ReportTab might not have a load method, just pass for now
                pass
                
            logger.info("Refreshed all tabs")
        except Exception as e:
            logger.error(f"Error refreshing tabs: {e}")
    
    def dong_ca_in_pdf(self):
        """Đóng ca và in tổng kết - Migrated from main_gui.py"""
        if not self.nhan_hang_completed:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self, "Lỗi", "Bạn chưa nhận hàng. Vui lòng nhận hàng trước khi đóng ca."
            )
            return

        from datetime import datetime
        from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
        from PyQt5.QtWidgets import QDialog, QTextEdit, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox
        from gui.file_helpers import tao_thu_muc_luu_tru, xoa_file_cu
        from gui.utils import format_price
        from invoices import lay_chi_tiet_hoadon
        from users import lay_tong_nop_theo_hoadon, lay_username
        from db import ket_noi
        import os

        # Lấy dữ liệu nhận hàng với chênh lệch
        nhan_hang_data = []
        chenh_lech_data = []
        
        if hasattr(self.tab_nhan_hang, 'tbl_nhan_hang'):
            tbl_nhan_hang = self.tab_nhan_hang.tbl_nhan_hang
            for row in range(tbl_nhan_hang.rowCount()):
                ten_item = tbl_nhan_hang.item(row, 0)
                if not ten_item:
                    continue
                ten_sp = ten_item.text()
                try:
                    sl_dem = float(tbl_nhan_hang.item(row, 1).text() if tbl_nhan_hang.item(row, 1) else "0")
                except (ValueError, AttributeError):
                    sl_dem = 0
                try:
                    ton_db = float(tbl_nhan_hang.item(row, 2).text() if tbl_nhan_hang.item(row, 2) else "0")
                except (ValueError, AttributeError):
                    ton_db = 0
                try:
                    chenh = float(tbl_nhan_hang.item(row, 3).text() if tbl_nhan_hang.item(row, 3) else "0")
                except (ValueError, AttributeError):
                    chenh = 0
                ghi_chu = (
                    tbl_nhan_hang.item(row, 4).text()
                    if tbl_nhan_hang.item(row, 4)
                    else ""
                )

                if sl_dem > 0:
                    nhan_hang_data.append((ten_sp, sl_dem, ton_db, chenh, ghi_chu))
                    if abs(chenh) > 0.001:  # Có chênh lệch
                        chenh_lech_data.append((ten_sp, ton_db, sl_dem, chenh, ghi_chu))

        # Lấy dữ liệu bán hàng từ HÓA ĐƠN CUỐI CÙNG
        today = datetime.now().strftime("%Y-%m-%d")
        today_display = datetime.now().strftime("%d/%m/%Y %H:%M")

        # Dùng dict để gộp sản phẩm
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
            # Mở hộp thoại in
            printer = QPrinter(QPrinter.HighResolution)
            printer.setPageSize(QPrinter.A4)

            print_dialog = QPrintDialog(printer, preview_dialog)
            print_dialog.setWindowTitle("In báo cáo đóng ca")

            if print_dialog.exec_() == QPrintDialog.Accepted:
                content.document().print_(printer)

                # Lưu file HTML
                try:
                    _, tong_ket_dir = tao_thu_muc_luu_tru()
                    xoa_file_cu(tong_ket_dir, so_thang=3)

                    html_filename = f"tong_ket_ca_{self.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                    html_filepath = os.path.join(tong_ket_dir, html_filename)

                    with open(html_filepath, "w", encoding="utf-8") as f:
                        f.write(html_content)

                    print(f"Đã lưu file tổng kết: {html_filename}")
                except Exception as e:
                    print(f"Lỗi khi lưu file tổng kết: {e}")

                QMessageBox.information(preview_dialog, "Thành công", "Đã in báo cáo đóng ca!")

        def close_shift():
            reply = QMessageBox.question(
                preview_dialog,
                "Xác nhận đóng ca",
                "Bạn có chắc muốn đóng ca không? Tab Bán hàng sẽ bị khóa cho đến khi nhận hàng mới.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                # Lưu file tổng kết ca
                try:
                    _, tong_ket_dir = tao_thu_muc_luu_tru()
                    xoa_file_cu(tong_ket_dir, so_thang=3)

                    html_filename = f"tong_ket_ca_{self.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                    html_filepath = os.path.join(tong_ket_dir, html_filename)

                    with open(html_filepath, "w", encoding="utf-8") as f:
                        f.write(html_content)

                    print(f"Đã lưu file tổng kết: {html_filename}")
                except Exception as e:
                    print(f"Lỗi khi lưu file tổng kết: {e}")

                # Mark shift as closed and disable selling
                self.ca_closed = True
                if hasattr(self, 'tab_banhang'):
                    self.tab_banhang.setEnabled(False)
                    if hasattr(self.tab_banhang, 'btn_luu'):
                        self.tab_banhang.btn_luu.setEnabled(False)
                
                # Reset receive state to allow new receiving
                self.nhan_hang_completed = False
                if hasattr(self, 'tab_nhan_hang'):
                    self.tab_nhan_hang.setEnabled(True)
                    # Xóa dữ liệu trong bảng nhận hàng
                    if hasattr(self.tab_nhan_hang, 'tbl_nhan_hang'):
                        self.tab_nhan_hang.tbl_nhan_hang.setRowCount(0)

                preview_dialog.accept()
                QMessageBox.information(
                    self,
                    "Thành công",
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
    
    def doi_mat_khau(self):
        """Đổi mật khẩu cho user hiện tại"""
        from db import ket_noi
        import hashlib
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Đổi mật khẩu")
        dialog.resize(400, 250)
        
        layout = QVBoxLayout()
        
        # Old password
        layout.addWidget(QLabel("Mật khẩu cũ:"))
        txt_old = QLineEdit()
        txt_old.setEchoMode(QLineEdit.Password)
        layout.addWidget(txt_old)
        
        # New password
        layout.addWidget(QLabel("Mật khẩu mới:"))
        txt_new = QLineEdit()
        txt_new.setEchoMode(QLineEdit.Password)
        layout.addWidget(txt_new)
        
        # Confirm password
        layout.addWidget(QLabel("Xác nhận mật khẩu mới:"))
        txt_confirm = QLineEdit()
        txt_confirm.setEchoMode(QLineEdit.Password)
        layout.addWidget(txt_confirm)
        
        # Buttons
        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Hủy")
        
        def change_password():
            old_pass = txt_old.text()
            new_pass = txt_new.text()
            confirm_pass = txt_confirm.text()
            
            if not old_pass or not new_pass:
                QMessageBox.warning(dialog, "Lỗi", "Vui lòng điền đầy đủ thông tin")
                return
            
            if new_pass != confirm_pass:
                QMessageBox.warning(dialog, "Lỗi", "Mật khẩu mới không khớp")
                return
            
            # Verify old password and change
            try:
                conn = ket_noi()
                c = conn.cursor()
                
                # Check old password
                c.execute("SELECT password FROM Users WHERE id=?", (self.user_id,))
                row = c.fetchone()
                if not row:
                    QMessageBox.warning(dialog, "Lỗi", "Không tìm thấy user")
                    conn.close()
                    return
                
                old_pass_hash = hashlib.sha256(old_pass.encode()).hexdigest()
                if row[0] != old_pass_hash:
                    QMessageBox.warning(dialog, "Lỗi", "Mật khẩu cũ không đúng")
                    conn.close()
                    return
                
                # Update new password
                new_pass_hash = hashlib.sha256(new_pass.encode()).hexdigest()
                c.execute("UPDATE Users SET password=? WHERE id=?", (new_pass_hash, self.user_id))
                conn.commit()
                conn.close()
                
                QMessageBox.information(dialog, "Thành công", "Đã đổi mật khẩu thành công!")
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(dialog, "Lỗi", f"Lỗi đổi mật khẩu: {e}")
        
        btn_ok.clicked.connect(change_password)
        btn_cancel.clicked.connect(dialog.reject)
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)
        
        dialog.setLayout(layout)
        dialog.exec_()

    def dang_xuat(self):
        """Đăng xuất và quay về màn hình đăng nhập"""
        reply = QMessageBox.question(
            self,
            "Xác nhận",
            "Bạn có chắc muốn đăng xuất?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.close()
            if self.login_window:
                self.login_window.show()
                # Clear login fields
                if hasattr(self.login_window, 'txt_username'):
                    self.login_window.txt_username.clear()
                if hasattr(self.login_window, 'txt_password'):
                    self.login_window.txt_password.clear()
    
    def closeEvent(self, event):
        """Override close event"""
        # Khi đóng từ nút "X", hỏi có muốn đăng xuất không
        reply = QMessageBox.question(
            self,
            "Xác nhận",
            "Đóng cửa sổ sẽ đăng xuất. Bạn có chắc?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Đăng xuất - hiện login window
            if self.login_window:
                self.login_window.show()
                # Clear  login fields
                if hasattr(self.login_window, 'txt_username'):
                    self.login_window.txt_username.clear()
                if hasattr(self.login_window, 'txt_password'):
                    self.login_window.txt_password.clear()
            event.accept()
        else:
            event.ignore()
