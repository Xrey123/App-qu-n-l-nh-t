import locale
from PyQt5.QtWidgets import QStyledItemDelegate, QLineEdit, QHeaderView
from PyQt5.QtCore import Qt

# Định dạng giá
locale.setlocale(locale.LC_ALL, "en_US.UTF-8")

def setup_table(table_widget):
    """Thiết lập bảng để hiển thị đầy đủ các cột"""
    # Tự động điều chỉnh độ rộng cột
    table_widget.horizontalHeader().setStretchLastSection(True)
    table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

    # Đảm bảo bảng có thể cuộn ngang nếu cần
    table_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    table_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    # Không dùng màu nền thay thế — giữ mặc định
    table_widget.setAlternatingRowColors(False)
    # Tăng chiều cao dòng mặc định để nội dung dễ nhìn hơn
    try:
        table_widget.verticalHeader().setDefaultSectionSize(26)  # giảm từ 30
    except Exception:
        pass

    # Tự động stretch cột chứa "Tên" hoặc "Sản phẩm" và resize các cột khác về nội dung
    try:
        header = table_widget.horizontalHeader()
        product_col_index = -1

        # Tìm cột có tên chứa "sản phẩm" hoặc "tên"
        for col in range(table_widget.columnCount()):
            header_text = table_widget.horizontalHeaderItem(col)
            if header_text:
                text = header_text.text().lower()
                if "sản phẩm" in text or ("tên" in text and "username" not in text):
                    product_col_index = col
                    break

        # Nếu tìm thấy cột sản phẩm, set stretch cho cột đó
        if product_col_index >= 0:
            for col in range(table_widget.columnCount()):
                if col == product_col_index:
                    header.setSectionResizeMode(col, QHeaderView.Stretch)
                else:
                    header.setSectionResizeMode(col, QHeaderView.ResizeToContents)
    except Exception as e:
        print(f"Warning: Could not auto-resize columns: {e}")

def format_price(value):
    try:
        return locale.format_string("%.2f", value, grouping=True)
    except Exception as e:
        print(f"Warning: Error formatting price {value}: {e}")
        return str(value)

class CompleterDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.completer = None

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        if self.completer:
            editor.setCompleter(self.completer)
            # Set completion mode to popup
            from PyQt5.QtWidgets import QCompleter
            self.completer.setCompletionMode(QCompleter.PopupCompletion)
            # Show popup when text changes
            editor.textChanged.connect(lambda: self.show_completer(editor))
        return editor
    
    def show_completer(self, editor):
        """Show completer popup"""
        if self.completer and editor.text():
            self.completer.setCompletionPrefix(editor.text())
            self.completer.complete()
