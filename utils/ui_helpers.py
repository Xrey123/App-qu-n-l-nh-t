"""
Helper functions for UI components
Các hàm tiện ích cho giao diện người dùng
"""
from PyQt5.QtWidgets import (
    QMessageBox, QTableWidget, QTableWidgetItem, 
    QDoubleSpinBox, QTreeWidget, QTreeWidgetItem
)


def show_error(parent, title, message):
    """Hiển thị thông báo lỗi"""
    QMessageBox.warning(parent, title, message)


def show_info(parent, title, message):
    """Hiển thị thông báo thông tin"""
    QMessageBox.information(parent, title, message)


def show_success(parent, message):
    """Hiển thị thông báo thành công"""
    QMessageBox.information(parent, "Thành công", message)


def show_warning(parent, message):
    """Hiển thị thông báo cảnh báo"""
    QMessageBox.warning(parent, "Cảnh báo", message)


def show_confirmation(parent, message):
    """
    Hiển thị hộp thoại xác nhận
    
    Returns:
        True nếu user click Yes/OK, False nếu click No/Cancel
    """
    reply = QMessageBox.question(
        parent, 
        "Xác nhận", 
        message,
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
    )
    return reply == QMessageBox.Yes


def create_table_item(value):
    """
    Tạo QTableWidgetItem từ giá trị
    Tự động chuyển đổi kiểu dữ liệu
    """
    return QTableWidgetItem(str(value))


def setup_quantity_spinbox(spinbox, decimals=5, maximum=1000000):
    """
    Cấu hình QDoubleSpinBox cho nhập số lượng
    
    Args:
        spinbox: QDoubleSpinBox widget
        decimals: Số chữ số thập phân (mặc định 5)
        maximum: Giá trị tối đa (mặc định 1,000,000)
    """
    spinbox.setDecimals(decimals)
    spinbox.setMaximum(maximum)
    spinbox.setMinimum(0)
    spinbox.setSingleStep(0.1)


def clear_table(table_widget):
    """Xóa tất cả dữ liệu trong QTableWidget"""
    table_widget.setRowCount(0)


def get_selected_rows(table_widget):
    """
    Lấy danh sách các dòng được chọn trong table
    
    Returns:
        List các số thứ tự dòng được chọn
    """
    selected_rows = set()
    for item in table_widget.selectedItems():
        selected_rows.add(item.row())
    return sorted(list(selected_rows))


def get_checked_rows(table_widget, checkbox_column=0):
    """
    Lấy danh sách các dòng có checkbox được tích
    
    Args:
        table_widget: QTableWidget
        checkbox_column: Cột chứa checkbox (mặc định 0)
        
    Returns:
        List các số thứ tự dòng được tích
    """
    from PyQt5.QtCore import Qt
    checked_rows = []
    for row in range(table_widget.rowCount()):
        item = table_widget.item(row, checkbox_column)
        if item and item.checkState() == Qt.Checked:
            checked_rows.append(row)
    return checked_rows


def populate_tree_widget(tree_widget, data, columns):
    """
    Điền dữ liệu vào QTreeWidget theo cấu trúc parent-child
    
    Args:
        tree_widget: QTreeWidget
        data: Dict với cấu trúc {parent_key: [child_rows]}
        columns: List tên các cột
    """
    tree_widget.clear()
    tree_widget.setColumnCount(len(columns))
    tree_widget.setHeaderLabels(columns)
    
    for parent_key, children in data.items():
        parent = QTreeWidgetItem(tree_widget)
        # Set parent data
        if isinstance(parent_key, (list, tuple)):
            for i, val in enumerate(parent_key):
                parent.setText(i, str(val))
        else:
            parent.setText(0, str(parent_key))
            
        # Add children
        for child_data in children:
            child = QTreeWidgetItem(parent)
            for i, val in enumerate(child_data):
                child.setText(i, str(val))


def safe_get_table_value(table_widget, row, col, default=""):
    """
    Lấy giá trị từ table một cách an toàn
    
    Args:
        table_widget: QTableWidget
        row: Số thứ tự dòng
        col: Số thứ tự cột
        default: Giá trị mặc định nếu không lấy được
        
    Returns:
        Giá trị trong ô hoặc giá trị mặc định
    """
    try:
        item = table_widget.item(row, col)
        if item:
            return item.text()
        return default
    except Exception:
        return default


def safe_get_widget_value(table_widget, row, col, default=None):
    """
    Lấy giá trị từ widget trong table cell
    
    Args:
        table_widget: QTableWidget
        row: Số thứ tự dòng
        col: Số thứ tự cột
        default: Giá trị mặc định
        
    Returns:
        Giá trị từ widget hoặc giá trị mặc định
    """
    try:
        widget = table_widget.cellWidget(row, col)
        if widget:
            if isinstance(widget, QDoubleSpinBox):
                return widget.value()
            elif hasattr(widget, 'text'):
                return widget.text()
            elif hasattr(widget, 'currentText'):
                return widget.currentText()
        return default
    except Exception:
        return default
