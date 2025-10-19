@echo off
echo ===============================
echo 🔄 GIT AUTO PULL STARTING...
echo ===============================

:: Kiểm tra Git repo
git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    echo ❌ Không tìm thấy Git repository trong thư mục này.
    pause
    exit /b
)

:: Kéo code mới
git pull
if errorlevel 1 (
    echo ❌ Pull thất bại! Có thể bạn có thay đổi chưa commit hoặc mạng yếu.
) else (
    echo ✅ Đã pull code mới nhất từ GitHub!
)

pause