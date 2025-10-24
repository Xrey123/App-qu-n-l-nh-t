@echo off
echo ===============================
echo 🚀 GIT AUTO PUSH STARTING...
echo ===============================

:: Kiểm tra Git repo
git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    echo ❌ Không tìm thấy Git repository trong thư mục này.
    pause
    exit /b
)

:: Thêm tất cả thay đổi
git add .

:: Commit với thời gian
set "msg=Auto save on %date% %time%"
git commit -m "%msg%" >nul 2>&1
git push