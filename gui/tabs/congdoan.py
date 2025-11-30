from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QDateEdit, 
    QPushButton, QTreeWidget, QTreeWidgetItem, QDialog, QLineEdit, QMessageBox, QTextEdit
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QDoubleValidator, QPainter
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog

from db import ket_noi
from utils.money import format_price
from utils.ui_helpers import show_error, show_success
from users import lay_tat_ca_user, chuyen_tien
from datetime import datetime

class CongDoanTab(QWidget):
    def __init__(self, user_id, main_window):
        super().__init__()
        self.user_id = user_id
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Lọc theo ngày và username
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("User:"))
        self.cd_user_combo = QComboBox()
        self.cd_user_combo.addItem("Tất cả", None)
        
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

        self.setLayout(layout)

    def load_bao_cao_cong_doan(self):
        """Load báo cáo công đoàn từ bảng ChenhLechXuatBo - hiển thị theo nhóm xuất bổ"""
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
                key = (
                    r[0],
                    r[2],
                    r[3],
                    r[4],
                )  # username, ngay_xuat, ten_sp, loai_gia_xuat
                groups[key].append(r)

            tong_chenh_lech_tat_ca = 0
            for key, details in groups.items():
                username, ngay_xuat, ten_sp, loai_gia_xuat = key

                # Tính tổng cho dòng cha từ các dòng con
                tong_sl = sum(d[9] for d in details)  # d[9] = so_luong
                tong_gia_ban = sum(d[10] for d in details)  # d[10] = tong_gia_ban
                tong_gia_xuat = sum(d[11] for d in details)  # d[11] = tong_gia_xuat
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
                    nhan = (
                        f"{loai_gia_nguon.upper()} {'MỚI' if is_gia_moi==1 else 'CŨ'}"
                    )
                    child.setText(0, nhan)
                    child.setText(1, "")
                    child.setText(2, "")
                    child.setText(3, f"{int(sl)}")
                    child.setText(
                        4, f"{format_price(gia_ban)}/sp → {format_price(gia_ban_tong)}"
                    )
                    child.setText(
                        5,
                        f"{format_price(gia_xuat)}/sp → {format_price(gia_xuat_tong)}",
                    )
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
            # Refresh if needed (e.g. if we had a balance display)
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
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)

        if dialog.exec_() == QPrintDialog.Accepted:
            text_edit = QTextEdit()
            text_edit.setHtml(html)
            text_edit.print_(printer)
            show_success(self, "Đã gửi báo cáo đến máy in")
