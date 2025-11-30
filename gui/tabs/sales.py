from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDateTimeEdit, QTableWidget, 
    QPushButton, QDoubleSpinBox, QComboBox, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, QDateTime, QTimer
from gui.utils import setup_table, format_price, CompleterDelegate
from utils.ui_helpers import show_error, show_success, show_info
from db import ket_noi
from products import tim_sanpham
from invoices import tao_hoa_don
from users import lay_tat_ca_user, chuyen_tien
import logging

logger = logging.getLogger(__name__)

def setup_quantity_spinbox(spinbox, decimals=2, maximum=9999):
    spinbox.setDecimals(decimals)
    spinbox.setMaximum(maximum)
    spinbox.setSingleStep(1)

def chon_don_gia(sp, so_luong, is_vip):
    # sp: [id, ten, gia_le, gia_buon, gia_vip, ton_kho, nguong_buon]
    gia_le = sp[2]
    gia_buon = sp[3]
    gia_vip = sp[4]
    nguong_buon = sp[6]

    if is_vip:
        return gia_vip
    if so_luong >= nguong_buon and nguong_buon > 0:
        return gia_buon
    return gia_le

def xac_dinh_loai_gia(so_luong, nguong_buon, is_vip):
    if is_vip:
        return "vip"
    if so_luong >= nguong_buon and nguong_buon > 0:
        return "buon"
    return "le"

class SalesTab(QWidget):
    def __init__(self, user_id, main_window):
        super().__init__()
        self.user_id = user_id
        self.main_window = main_window # Reference to MainWindow for callbacks/shared state
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Header with DateTime
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

        # Cart Table
        self.tbl_giohang = QTableWidget()
        self.tbl_giohang.setColumnCount(9)
        self.tbl_giohang.setHorizontalHeaderLabels(
            [
                "Tên", "SL", "Đơn giá", "Giảm giá", "Tổng tiền", 
                "VIP", "XHD", "Ghi chú", "Người cho nợ"
            ]
        )
        setup_table(self.tbl_giohang)
        self.tbl_giohang.setEditTriggers(QTableWidget.AllEditTriggers)
        
        # Completer Delegate
        delegate = CompleterDelegate(self)
        # Completer needs to be set from main window or shared source
        if hasattr(self.main_window, 'tao_completer_sanpham'):
             delegate.completer = self.main_window.tao_completer_sanpham()
        self.tbl_giohang.setItemDelegateForColumn(0, delegate)
        
        self.tbl_giohang.itemChanged.connect(self.update_giohang)
        layout.addWidget(self.tbl_giohang)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_them_dong = QPushButton("Thêm dòng")
        btn_them_dong.clicked.connect(self.them_dong_giohang)
        btn_layout.addWidget(btn_them_dong)
        
        self.btn_luu = QPushButton("Lưu")
        self.btn_luu.setEnabled(False) # Enabled only after receiving goods
        self.btn_luu.clicked.connect(self.tao_hoa_don_click)
        btn_layout.addWidget(self.btn_luu)

        btn_close_shift = QPushButton("Đóng ca (In tổng kết)")
        if hasattr(self.main_window, 'dong_ca_in_pdf'):
            btn_close_shift.clicked.connect(self.main_window.dong_ca_in_pdf)
        btn_layout.addWidget(btn_close_shift)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

        # Init empty rows
        for _ in range(15):
            self.them_dong_giohang()

    def them_dong_giohang(self):
        row = self.tbl_giohang.rowCount()
        self.tbl_giohang.insertRow(row)
        
        self.tbl_giohang.setItem(row, 0, QTableWidgetItem("")) # Tên
        
        sl_spin = QDoubleSpinBox()
        setup_quantity_spinbox(sl_spin, decimals=5, maximum=9999)
        sl_spin.setValue(1.0)
        sl_spin.valueChanged.connect(lambda: self.update_giohang_row(row))
        self.tbl_giohang.setCellWidget(row, 1, sl_spin)
        
        self.tbl_giohang.setItem(row, 2, QTableWidgetItem(format_price(0))) # Đơn giá
        
        giam_spin = QDoubleSpinBox()
        giam_spin.setMinimum(0)
        giam_spin.setMaximum(999999)
        giam_spin.setDecimals(2)
        giam_spin.setValue(0)
        giam_spin.valueChanged.connect(lambda: self.update_giohang_row(row))
        self.tbl_giohang.setCellWidget(row, 3, giam_spin)
        
        self.tbl_giohang.setItem(row, 4, QTableWidgetItem(format_price(0))) # Tổng tiền
        
        vip_item = QTableWidgetItem()
        vip_item.setCheckState(Qt.Unchecked)
        vip_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        self.tbl_giohang.setItem(row, 5, vip_item)
        
        xhd_item = QTableWidgetItem()
        xhd_item.setCheckState(Qt.Unchecked)
        xhd_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        self.tbl_giohang.setItem(row, 6, xhd_item)
        
        self.tbl_giohang.setItem(row, 7, QTableWidgetItem("")) # Ghi chú
        
        # Debt Combo
        cho_no_combo = QComboBox()
        cho_no_combo.addItem("-- Không --", None)
        try:
            users = lay_tat_ca_user()
            for user in users:
                if user[0] != self.user_id:
                    cho_no_combo.addItem(f"{user[1]}", user[0])
        except Exception as e:
            logger.error(f"Error loading users: {e}")
        self.tbl_giohang.setCellWidget(row, 8, cho_no_combo)

    def update_giohang_row(self, row):
        self.tbl_giohang.itemChanged.disconnect(self.update_giohang)
        
        ten_item = self.tbl_giohang.item(row, 0)
        ten = ten_item.text().strip() if ten_item else ""
        
        sl_spin = self.tbl_giohang.cellWidget(row, 1)
        sl = sl_spin.value() if sl_spin else 1.0
        
        don_gia_item = self.tbl_giohang.item(row, 2)
        try:
            don_gia = float(don_gia_item.text().replace(",", "")) if don_gia_item and don_gia_item.text() else 0
        except ValueError:
            don_gia = 0
            
        giam_spin = self.tbl_giohang.cellWidget(row, 3)
        giam_gia = giam_spin.value() if giam_spin else 0
        
        vip_item = self.tbl_giohang.item(row, 5)
        is_vip = vip_item.checkState() == Qt.Checked if vip_item else False

        if ten:
            res = tim_sanpham(ten)
            if res:
                sp = res[0]
                try:
                    don_gia = chon_don_gia(sp, sl, is_vip)
                    self.tbl_giohang.setItem(row, 2, QTableWidgetItem(format_price(don_gia)))
                except Exception:
                    pass
            else:
                # Product not found
                self.tbl_giohang.setItem(row, 2, QTableWidgetItem(format_price(0)))
                don_gia = 0
                self.tbl_giohang.setItem(row, 0, QTableWidgetItem("")) # Clear invalid name
                self.tbl_giohang.itemChanged.connect(self.update_giohang)
                return

        # Check availability (using main_window shared state)
        if ten and hasattr(self.main_window, 'available_products'):
            avail_qty = self.main_window.available_products.get(ten, 0)
            if avail_qty <= 0:
                show_error(self, "Lỗi", f"Sản phẩm '{ten}' chưa được nhận hàng")
                self.tbl_giohang.setItem(row, 0, QTableWidgetItem(""))
                self.tbl_giohang.setItem(row, 2, QTableWidgetItem(format_price(0)))
                self.tbl_giohang.itemChanged.connect(self.update_giohang)
                return

        tong_tien = sl * don_gia - giam_gia
        self.tbl_giohang.setItem(row, 4, QTableWidgetItem(format_price(tong_tien)))
        
        self.tbl_giohang.itemChanged.connect(self.update_giohang)

    def update_giohang(self, item):
        row = item.row()
        col = item.column()
        if col in [0, 5]: # Name or VIP changed
            self.update_giohang_row(row)

    def tao_hoa_don_click(self):
        items = []
        cho_no_items = []
        
        for row in range(self.tbl_giohang.rowCount()):
            ten_item = self.tbl_giohang.item(row, 0)
            if not (ten_item and ten_item.text()): continue
            
            sl_spin = self.tbl_giohang.cellWidget(row, 1)
            don_gia_item = self.tbl_giohang.item(row, 2)
            giam_spin = self.tbl_giohang.cellWidget(row, 3)
            vip_item = self.tbl_giohang.item(row, 5)
            xhd_item = self.tbl_giohang.item(row, 6)
            ghi_chu_item = self.tbl_giohang.item(row, 7)
            cho_no_combo = self.tbl_giohang.cellWidget(row, 8)
            
            ten = ten_item.text().strip()
            res = tim_sanpham(ten)
            if not res:
                show_error(self, "Lỗi", f"Sản phẩm '{ten}' không tồn tại")
                return
                
            sanpham_id = res[0][0]
            so_luong = sl_spin.value()
            try:
                gia = float(don_gia_item.text().replace(",", ""))
            except ValueError:
                show_error(self, "Lỗi", f"Giá lỗi dòng {row+1}")
                return
            giam = giam_spin.value()
            
            is_vip = vip_item.checkState() == Qt.Checked
            loai_gia = xac_dinh_loai_gia(so_luong, res[0][6] if len(res[0]) > 6 else 0, is_vip)
            
            xhd = xhd_item.checkState() == Qt.Checked
            ghi_chu = ghi_chu_item.text().strip() if ghi_chu_item else ""
            
            cho_no_user_id = cho_no_combo.currentData()
            if cho_no_user_id is not None:
                if not ghi_chu:
                    show_error(self, "Lỗi", f"Dòng {row+1}: Cần ghi chú khi cho nợ")
                    return
                tong_tien = so_luong * gia - giam
                cho_no_items.append({
                    "user_id": cho_no_user_id,
                    "so_tien": tong_tien,
                    "ghi_chu": ghi_chu,
                    "ten_sanpham": ten,
                    "so_luong": so_luong,
                    "gia": gia
                })
                
            items.append({
                "sanpham_id": sanpham_id,
                "so_luong": so_luong,
                "loai_gia": loai_gia,
                "gia": gia,
                "giam": giam,
                "xuat_hoa_don": xhd,
                "ghi_chu": ghi_chu
            })
            
        if not items:
            show_error(self, "Lỗi", "Giỏ hàng rỗng")
            return
            
        ngay_ghi_nhan = self.datetime_hoadon.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        
        try:
            success, msg, _ = tao_hoa_don(self.user_id, "", items, 0, 0, 0, ngay_ghi_nhan)
        except Exception as e:
            show_error(self, "Lỗi", f"Lỗi tạo hóa đơn: {e}")
            return
            
        if not success:
            show_error(self, "Lỗi", msg)
            return
        
        # ✅ FIX: CỘNG TIỀN VÀO SỐ DƯ USER BÁN HÀNG NGAY SAU KHI TẠO HÓA ĐƠN
        tong_tien_ban = sum(item["so_luong"] * item["gia"] - item["giam"] for item in items)
        
        try:
            conn = ket_noi()
            c = conn.cursor()
            
            # Cộng tiền vào số dư user
            c.execute("UPDATE Users SET so_du = so_du + ? WHERE id = ?", 
                     (tong_tien_ban, self.user_id))
            conn.commit()
            conn.close()
            
            logger.info(f"Added {tong_tien_ban} to user {self.user_id} balance")
        except Exception as e:
            logger.error(f"Error updating user balance: {e}")
            show_error(self, "Cảnh báo", f"Lưu hóa đơn thành công nhưng không cập nhật được số dư: {e}")
            
        # Update available stock in main window
        if hasattr(self.main_window, 'available_products'):
            for it in items:
                # Need name to update dict
                try:
                    conn = ket_noi()
                    c = conn.cursor()
                    c.execute("SELECT ten FROM SanPham WHERE id=?", (it["sanpham_id"],))
                    row = c.fetchone()
                    if row:
                        name = row[0]
                        prev = self.main_window.available_products.get(name, 0)
                        self.main_window.available_products[name] = max(0, prev - it["so_luong"])
                    conn.close()
                except Exception:
                    pass

        if hasattr(self.main_window, 'cap_nhat_completer_sanpham'):
            self.main_window.cap_nhat_completer_sanpham()
        
        # Store last invoice ID for close shift report
        try:
            self.main_window.last_invoice_id = int(msg)
        except:
            pass
        
        # ✅ REFRESH ALL TABS to update data
        if hasattr(self.main_window, 'refresh_all_tabs'):
            self.main_window.refresh_all_tabs()
            
        show_success(self, f"Tạo hóa đơn thành công, ID: {msg}\n💰 Đã cộng {format_price(tong_tien_ban)} vào số dư của bạn")
        
        # Handle Debt (cho nợ)
        if cho_no_items:
            users = lay_tat_ca_user()
            user_dict = {u[0]: u[1] for u in users}
            
            for cho_no in cho_no_items:
                try:
                    user_nhan_id = cho_no["user_id"]
                    so_tien = cho_no["so_tien"]
                    ghi_chu_full = f"[CHO NỢ] {cho_no['ghi_chu']} - {cho_no['ten_sanpham']} x{cho_no['so_luong']}"
                    
                    suc, m = chuyen_tien(self.user_id, user_nhan_id, so_tien)
                    if suc:
                        # Update note
                        try:
                            conn = ket_noi()
                            c = conn.cursor()
                            c.execute("""
                                SELECT id FROM GiaoDichQuy 
                                WHERE user_id = ? AND user_nhan_id = ? 
                                ORDER BY id DESC LIMIT 1
                            """, (self.user_id, user_nhan_id))
                            gd_row = c.fetchone()
                            if gd_row:
                                c.execute("UPDATE GiaoDichQuy SET ghi_chu = ? WHERE id = ?", (ghi_chu_full, gd_row[0]))
                                conn.commit()
                            conn.close()
                        except Exception:
                            pass
                    else:
                        show_error(self, "Lỗi cho nợ", f"Không thể chuyển tiền cho {user_dict.get(user_nhan_id, 'Unknown')}: {m}")
                except Exception as e:
                    logger.error(f"Error processing debt: {e}")
        
        # Clear cart
        self.tbl_giohang.setRowCount(0)
        for _ in range(15):
            self.them_dong_giohang()

        # Refresh other tabs if needed
        # Can implement signal/callback system for better decoupling later
        
        self.datetime_hoadon.setDateTime(QDateTime.currentDateTime())
        self.main_window.last_invoice_id = int(msg)
        
        self.tbl_giohang.setRowCount(0)
        for _ in range(15):
            self.them_dong_giohang()
