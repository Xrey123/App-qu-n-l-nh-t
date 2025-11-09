"""
Script to replace debug print() statements with logger calls in main_gui.py

This script will:
1. Replace debug prints with logger.debug()
2. Replace warning prints with logger.warning()
3. Replace error prints with logger.error()
"""

import re

# Read the file
with open('main_gui.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Count original prints
original_count = len(re.findall(r'^\s*print\(', content, re.MULTILINE))
print(f"Found {original_count} print statements")

# Patterns to replace
replacements = [
    # Debug prints (với # Debug comment)
    (r'print\(f"Added row.*?\)  # Debug', 'logger.debug(f"Added row {row} with default values")'),
    (r'print\(f"Updating row.*?\)  # Debug', 'logger.debug(f"Updating row {row}")'),
    (r'print\(f"Ten: .*?\)  # Debug', 'logger.debug(f"Ten: {ten}")'),
    (r'print\(f"SL: .*?\)  # Debug', 'logger.debug(f"SL: {sl}")'),
    (r'print\(f"Don gia \(before update\): .*?\)  # Debug', 'logger.debug(f"Don gia (before update): {don_gia}")'),
    (r'print\(f"Giam gia: .*?\)  # Debug', 'logger.debug(f"Giam gia: {giam_gia}")'),
    (r'print\(f"Is VIP: .*?\)  # Debug', 'logger.debug(f"Is VIP: {is_vip}")'),
    (r'print\(f"tim_sanpham.*?\)  # Debug', 'logger.debug(f"tim_sanpham({ten}) result: {res}")'),
    (r'print\(f"Selected don_gia: .*?\)  # Debug', 'logger.debug(f"Selected don_gia: {don_gia}")'),
    (r'print\(f"Invalid price data.*?\)  # Debug', 'logger.debug(f"Invalid price data for product \'{ten}\'")'),
    (r'print\(f"Sản phẩm.*?không tồn tại"\)  # Debug', 'logger.debug(f"Sản phẩm \'{ten}\' không tồn tại")'),
    (r'print\(f"Tong tien: .*?\)  # Debug', 'logger.debug(f"Tong tien: {tong_tien}")'),
    (r'print\(f"Error calculating.*?\)  # Debug', 'logger.debug(f"Error calculating tong_tien for row {row}")'),
    (r'print\(f"Item changed: .*?\)  # Debug', 'logger.debug(f"Item changed: row={row}, col={col}")'),
    
    # DEBUG BUON prints
    (r'print\(f"DEBUG BUON - Đủ.*?\)', 'logger.debug(f"XUATBO: Đủ từ bảng buôn")'),
    (r'print\(f"DEBUG BUON - Thiếu.*?\)', 'logger.debug(f"XUATBO: Thiếu {thieu}, cần lấy từ lẻ")'),
    (r'print\(f"DEBUG BUON - Sẽ xuất.*?\)', 'logger.debug(f"XUATBO: Sẽ xuất {sl_buon} từ buôn và {thieu} từ lẻ")'),
    
    # DEBUG XUẤT prints
    (r'print\(f"DEBUG XUẤT - \{ten\}.*?\)', 'logger.debug(f"XUATBO: {ten} ({loai_gia}):")'),
    (r'print\(f"  - Yêu cầu xuất: .*?\)', 'logger.debug(f"  - Yêu cầu xuất: {so_luong_xuat}")'),
    (r'print\(f"  - Còn phải xuất.*?\)', 'logger.debug(f"  - Còn phải xuất từ hóa đơn: {sl_xuat_hoadon}")'),
    
    # DEBUG XUẤT DƯ prints
    (r'print\(f"DEBUG XUẤT DƯ - \{ten\}:"\)', 'logger.debug(f"XUATDU: {ten}:")'),
    (r'print\(f"  - sl_can_xuat_chinh: .*?\)', 'logger.debug(f"  - sl_can_xuat_chinh: {sl_can_xuat_chinh}")'),
    (r'print\(f"  - sl_hd_phu \(\{loai_gia_phu\}\): .*?\)', 'logger.debug(f"  - sl_hd_phu ({loai_gia_phu}): {sl_hd_phu}")'),
    (r'print\(f"  - sl_hd_phu2 \(\{loai_gia_phu2\}\): .*?\)', 'logger.debug(f"  - sl_hd_phu2 ({loai_gia_phu2}): {sl_hd_phu2}")'),
    (r'print\(f"  - sl_co_the_xuat.*?\)', 'logger.debug(f"  - sl_co_the_xuat (TONG THUC TE): {sl_co_the_xuat}")'),
    (r'print\(f"  - du \(SO AM CAN TAO\): .*?\)', 'logger.debug(f"  - du (SO AM CAN TAO): {du}")'),
    
    # Warning prints
    (r'print\(f"Warning: Error formatting price.*?\)', 'logger.warning(f"Error formatting price {value}: {e}")'),
    (r'print\(f"Warning: Could not load username.*?\)', 'logger.warning(f"Could not load username for user_id {user_id}: {e}")'),
    (r'print\(f"Warning: Could not auto-resize.*?\)', 'logger.warning(f"Could not auto-resize columns: {e}")'),
    (r'print\(f"Warning: Could not close connection.*?\)', 'logger.warning(f"Could not close connection: {close_err}")'),
    (r'print\(f"Warning: Could not parse.*?\)', 'logger.warning(f"Could not parse money value at row {row}: {e}")'),
    (r'print\(f"Warning: Invalid quantity.*?\)', 'logger.warning(f"Invalid quantity at row {row}: {e}")'),
    (r'print\(f"Warning: Invalid stock.*?\)', 'logger.warning(f"Invalid stock at row {row}: {e}")'),
    (r'print\(f"Warning: Invalid difference.*?\)', 'logger.warning(f"Invalid difference at row {row}: {e}")'),
    (r'print\(f"Warning: Could not load tong_cong_doan.*?\)', 'logger.warning(f"Could not load tong_cong_doan: {e}")'),
    (r'print\(f"Warning: Could not close/rollback.*?\)', 'logger.warning(f"Could not close/rollback connection: {close_err}")'),
    
    # Error/Info prints  
    (r'print\(f"Đã xóa file cũ: .*?\)', 'logger.info(f"Deleted old file: {filename} ({so_ngay_cu} days old)")'),
    (r'print\(f"Lỗi khi xóa file cũ: .*?\)', 'logger.error(f"Error deleting old file: {e}")'),
    (r'print\(f"Logo loading error: .*?\)', 'logger.error(f"Logo loading error: {e}")'),
    (r'print\(f"Không thể load logo: .*?\)', 'logger.error(f"Cannot load logo: {e}")'),
    (r'print\(f"Không thể hiển thị logo: .*?\)', 'logger.error(f"Cannot display logo: {e}")'),
    (r'print\(f"❌ Chi tiết lỗi AI: .*?\)', 'logger.error(f"AI error details: {e}", exc_info=True)'),
    (r'print\(f"⚠️ Tab Home init: .*?\)', 'logger.error(f"Tab Home init failed: {e}")'),
    (r'print\(f"Lỗi load user.*?\)', 'logger.error(f"Error loading users for combo: {e}")'),
    (r'print\(f"Items before tao_hoa_don: .*?\)', 'logger.debug(f"Items before tao_hoa_don: {items}")'),
    (r'print\(f"Ngày ghi nhận: .*?\)', 'logger.debug(f"Ngày ghi nhận: {ngay_ghi_nhan}")'),
    (r'print\(f"Error calling tao_hoa_don: .*?\)', 'logger.error(f"Error calling tao_hoa_don: {e}", exc_info=True)'),
    (r'print\(f"tao_hoa_don failed: .*?\)', 'logger.error(f"tao_hoa_don failed: {msg}")'),
    (r'print\(f"✅ Chuyển nợ: .*?\)', 'logger.info(f"Chuyển nợ: {format_price(so_tien)} → {user_nhan_name}")'),
    (r'print\(f"   Ghi chú: .*?\)', 'logger.info(f"   Ghi chú: {ghi_chu_full}")'),
    (r'print\(f"⚠️ Không thể cập nhật ghi chú.*?\)', 'logger.warning(f"Cannot update transaction note: {e}")'),
    (r'print\(f"⚠️ Lỗi chuyển nợ: .*?\)', 'logger.error(f"Error transferring debt: {msg_transfer}")'),
    (r'print\(f"⚠️ Lỗi xử lý cho nợ: .*?\)', 'logger.error(f"Error processing debt: {e}")'),
    (r'print\(f"⚠️ Không thể load chi tiết bán: .*?\)', 'logger.warning(f"Cannot load sales details: {e}")'),
    (r'print\(f"⚠️ Không thể load hóa đơn: .*?\)', 'logger.warning(f"Cannot load invoices: {e}")'),
    (r'print\(f"⚠️ Không thể load sổ quỹ: .*?\)', 'logger.warning(f"Cannot load fund ledger: {e}")'),
    (r'print\(f"⚠️ Không thể load lịch sử giao dịch: .*?\)', 'logger.warning(f"Cannot load transaction history: {e}")'),
    (r'print\(f"⚠️ Không thể load Tab Home: .*?\)', 'logger.warning(f"Cannot load Tab Home: {e}")'),
    (r'print\(f"Lỗi load XHD data: .*?\)', 'logger.error(f"Error loading XHD data: {e}")'),
    (r'print\(f"Lỗi đăng xuất: .*?\)', 'logger.error(f"Logout error: {e}")'),
    (r'print\(f"Đã lưu file tổng kết: .*?\)', 'logger.info(f"Saved summary file: {html_filename}")'),
    (r'print\(f"Lỗi khi lưu file tổng kết: .*?\)', 'logger.error(f"Error saving summary file: {e}")'),
    (r'print\(f"DB init error: .*?\)', 'logger.error(f"Database init error: {e}", exc_info=True)'),
]

# Apply replacements
for pattern, replacement in replacements:
    content = re.sub(pattern, replacement, content)

# Count remaining prints
remaining_count = len(re.findall(r'^\s*print\(', content, re.MULTILINE))

print(f"Replaced {original_count - remaining_count} print statements")
print(f"Remaining: {remaining_count} print statements")

# Write back
with open('main_gui.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Done! Check main_gui.py")
