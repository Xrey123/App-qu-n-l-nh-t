"""
File helper utilities for managing data export directories
Migrated from main_gui.py
"""
import os
from datetime import datetime


def tao_thu_muc_luu_tru():
    """Tạo thư mục để lưu file nhận hàng và tổng kết ca"""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    data_dir = os.path.join(base_dir, "data_export")
    nhan_hang_dir = os.path.join(data_dir, "nhan_hang")
    tong_ket_dir = os.path.join(data_dir, "tong_ket_ca")

    # Tạo các thư mục nếu chưa tồn tại
    os.makedirs(nhan_hang_dir, exist_ok=True)
    os.makedirs(tong_ket_dir, exist_ok=True)

    return nhan_hang_dir, tong_ket_dir


def xoa_file_cu(thu_muc, so_thang=3):
    """Xóa các file cũ hơn số tháng chỉ định trong thư mục"""
    try:
        ngay_hien_tai = datetime.now()
        so_ngay = so_thang * 30  # Tương đương số tháng

        for filename in os.listdir(thu_muc):
            filepath = os.path.join(thu_muc, filename)

            # Chỉ xóa file, không xóa thư mục
            if os.path.isfile(filepath):
                # Lấy thời gian sửa đổi file
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))

                # Tính số ngày từ file đến hiện tại
                so_ngay_cu = (ngay_hien_tai - file_time).days

                # Xóa nếu file cũ hơn số tháng chỉ định
                if so_ngay_cu > so_ngay:
                    os.remove(filepath)
                    print(f"Đã xóa file cũ: {filename} ({so_ngay_cu} ngày)")
    except Exception as e:
        print(f"Lỗi khi xóa file cũ: {e}")
