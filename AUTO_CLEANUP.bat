@echo off
echo =========================================
echo   AUTO CLEANUP - TU DONG XOA FILE DU THUA
echo =========================================
echo.
echo [1/3] Tao thu muc backup...
if not exist "backup_old_files" mkdir backup_old_files

echo [2/3] Backup va xoa cac file...

if exist demo_ai_features.py (
    echo   - demo_ai_features.py
    move demo_ai_features.py backup_old_files\ >nul 2>&1
)

if exist demo_chi_tiet_ban.py (
    echo   - demo_chi_tiet_ban.py
    move demo_chi_tiet_ban.py backup_old_files\ >nul 2>&1
)

if exist test_ai_database_security.py (
    echo   - test_ai_database_security.py
    move test_ai_database_security.py backup_old_files\ >nul 2>&1
)

if exist test_direct_db_query.py (
    echo   - test_direct_db_query.py
    move test_direct_db_query.py backup_old_files\ >nul 2>&1
)

if exist test_zalo_notification.py (
    echo   - test_zalo_notification.py
    move test_zalo_notification.py backup_old_files\ >nul 2>&1
)

if exist migration_add_phone.py (
    echo   - migration_add_phone.py
    move migration_add_phone.py backup_old_files\ >nul 2>&1
)

if exist update_user_phones.py (
    echo   - update_user_phones.py
    move update_user_phones.py backup_old_files\ >nul 2>&1
)

if exist quick_update_phones.py (
    echo   - quick_update_phones.py
    move quick_update_phones.py backup_old_files\ >nul 2>&1
)

if exist fix_debug_prints.py (
    echo   - fix_debug_prints.py
    move fix_debug_prints.py backup_old_files\ >nul 2>&1
)

if exist START_APP_SIMPLE.bat (
    echo   - START_APP_SIMPLE.bat
    move START_APP_SIMPLE.bat backup_old_files\ >nul 2>&1
)

if exist CLEANUP_FINAL_COMPLETE.bat (
    echo   - CLEANUP_FINAL_COMPLETE.bat
    move CLEANUP_FINAL_COMPLETE.bat backup_old_files\ >nul 2>&1
)

echo.
echo [3/3] Hoan tat!
echo.
echo =========================================
echo   THANH CONG!
echo.
echo   Cac file da duoc chuyen vao:
echo   backup_old_files\
echo.
echo   Neu can khoi phuc, copy lai tu thu muc nay
echo =========================================
