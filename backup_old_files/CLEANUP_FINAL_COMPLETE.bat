@echo off
REM =============================================
REM  CLEANUP FINAL - Xóa HOÀN TOÀN mọi file rác
REM =============================================

echo =========================================
echo   CLEANUP FINAL - XOA TAT CA FILE RAC
echo =========================================
echo.

echo [1/8] Xóa Python cache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
del /s /q *.pyc 2>nul
echo      Done!
echo.

echo [2/8] Xóa file .py KHÔNG CẦN THIẾT...
del /q fix_xuat_bo_to_bo.py 2>nul
del /q replace_xuat_bo.py 2>nul
del /q test_cleanup.py 2>nul
del /q update_don_vi.py 2>nul
echo      Done!
echo.

echo [3/8] Xóa THƯ MỤC DOCS cũ...
rd /s /q docs 2>nul
echo      Done!
echo.

echo [4/8] Xóa THƯ MỤC LLAMA.CPP (không dùng)...
rd /s /q llama.cpp 2>nul
echo      Done!
echo.

echo [5/8] Xóa THƯ MỤC MODELS (đã xóa model)...
rd /s /q models 2>nul
echo      Done!
echo.

echo [6/8] Xóa batch files cũ...
del /q CLEANUP_ALL.bat 2>nul
del /q CLEANUP_COMPLETE.bat 2>nul
del /q START_CLEAN.bat 2>nul
del /q menu.bat 2>nul
echo      Done!
echo.

echo [7/8] Giữ lại CHỈ file cần thiết trong scripts/...
echo      (Giữ: add_admin.py)
echo      Done!
echo.

echo [8/8] Xóa file HUONG_DAN_GROQ_API.md (đã biết rồi)...
REM Keep this - may need later
echo      Skip (giữ lại)
echo.

echo =========================================
echo   HOAN THANH! Project cực kỳ sạch sẽ
echo =========================================
echo.
echo FILES GIỮ LẠI:
echo   ✅ main_gui.py (App chính)
echo   ✅ start.py (Launcher)
echo   ✅ db.py, products.py, invoices.py, reports.py, stock.py, users.py, shortcuts.py
echo   ✅ ai_system/ (hybrid.py, actions.py, permissions.py)
echo   ✅ ai/ (JSON configs)
echo   ✅ utils/ (helpers)
echo   ✅ fapp.db (Database)
echo   ✅ START_APP_SIMPLE.bat
echo   ✅ HUONG_DAN_GROQ_API.md
echo.
echo ❌ ĐÃ XÓA:
echo   ❌ docs/ (10+ MD files)
echo   ❌ llama.cpp/ (không dùng Ollama local server nữa)
echo   ❌ models/ (đã xóa Gemma2, Qwen)
echo   ❌ test_*.py, fix_*.py, replace_*.py
echo   ❌ __pycache__/
echo.
pause
