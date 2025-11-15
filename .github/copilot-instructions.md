
# Hướng dẫn Copilot cho AI Coding Agents

## Tổng quan dự án
Dự án này là ứng dụng desktop quản lý cửa hàng/kho, viết bằng Python, có giao diện GUI, thao tác cơ sở dữ liệu, báo cáo, và quy trình hỗ trợ AI. Mã nguồn được tổ chức theo từng chức năng (GUI, database, AI, tiện ích, xuất dữ liệu...).

## Kiến trúc & Thành phần chính
- **main_gui.py**: Điểm khởi động ứng dụng GUI. Quản lý tương tác người dùng và cập nhật giao diện.
- **db.py**: Xử lý thao tác cơ sở dữ liệu. Mọi truy cập dữ liệu đều qua module này.
- **ai/**: Chứa cấu hình AI (`config.json`) và các mẫu prompt cho từng vai trò người dùng. Dùng cho các tính năng AI và tích hợp.
- **ai_system/**: Hiện thực logic AI, quản lý prompt và bộ nhớ (ví dụ: `actions.py`, `langchain_memory.py`).
- **reports.py, stock.py, users.py**: Các module nghiệp vụ cho báo cáo, kho, quản lý người dùng.
- **utils/**: Hàm tiện ích dùng chung.
- **data_export/**: Quản lý backup và xuất dữ liệu, phân loại theo từng loại.

## Quy trình phát triển
- **Chạy GUI**: Dùng `RUN_GUI.bat` hoặc chạy trực tiếp `main_gui.py`.
- **Đóng gói file thực thi**: Dùng `ShopFlow.spec` với PyInstaller để build.
- **Kiểm thử**: Chạy các script như `test_db_actions.py`, `test_nhap_kho.py` để kiểm tra logic database/kho. Không phát hiện test runner chính thức, chỉ chạy script trực tiếp.
- **Cấu hình**: Hành vi AI cấu hình qua `ai/config.json` và các file prompt trong `ai/prompts/`.

## Quy ước đặc thù
- **AI Prompts**: Mẫu prompt chia theo vai trò trong `ai/prompts/` (ví dụ: `accountant.txt`, `expert.txt`).
- **Thiết kế module hóa**: Mỗi chức năng (AI, DB, GUI...) tách riêng để dễ bảo trì.
- **Script batch**: Các file `.bat` (`RUN_GUI.bat`, `push.bat`) dùng cho thao tác nhanh trên Windows.
- **Không dùng ORM**: Truy cập database trực tiếp (xem `db.py`).

## Điểm tích hợp
- **Hệ thống AI**: Tích hợp dịch vụ AI ngoài qua các module trong `ai_system/` và quản lý prompt.
- **Xuất dữ liệu**: Backup và xuất dữ liệu tự động qua `data_export/`.
- **Báo cáo**: Logic báo cáo tùy chỉnh trong `reports.py`.

## Quy ước & Ví dụ
- **Quản lý prompt**: Dùng `ai_system/prompt_manager.py` để load và quản lý prompt AI.
- **Quản lý bộ nhớ AI**: Xem `ai_system/langchain_memory.py` để xử lý trạng thái/bộ nhớ AI.
- **Kiểm thử**: Ví dụ: `python test_db_actions.py` để kiểm tra logic DB.
- **Chạy GUI**: Ví dụ: `RUN_GUI.bat` hoặc `python main_gui.py`.

## File & thư mục quan trọng
- `main_gui.py`, `db.py`, `ai/`, `ai_system/`, `reports.py`, `stock.py`, `users.py`, `utils/`, `data_export/`

---

**Phản hồi cần thiết:**
- Có quy trình, tích hợp, quy ước nào còn thiếu hoặc chưa rõ?
- Có logic hoặc mẫu nào chưa được ghi chú?
- Vui lòng chỉ rõ phần cần tài liệu hoặc ví dụ chi tiết hơn.
