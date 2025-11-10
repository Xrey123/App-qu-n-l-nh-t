@echo off
chcp 65001 >nul
title START APP + AI HYBRID

echo ========================================
echo   KHOI DONG APP + AI HYBRID
echo ========================================
echo.
echo AI System: Qwen2-1.5B + Gemma 2B
echo.

REM Kiem tra Ollama
echo [1/4] Kiem tra Ollama (Qwen2-1.5B)...
where ollama >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Ollama da cai
    
    REM Kiem tra Ollama service
    ollama list >nul 2>&1
    if %errorlevel% == 0 (
        echo [OK] Ollama dang chay
    ) else (
        echo [INFO] Dang khoi dong Ollama...
        start "" ollama serve
        timeout /t 3 >nul
    )
    
    REM Kiem tra model Qwen2-1.5B
    ollama list | findstr "qwen2:1.5b" >nul 2>&1
    if %errorlevel% == 0 (
        echo [OK] Qwen2-1.5B san sang
    ) else (
        echo [WARN] Qwen2 chua co, dung Gemma backup
    )
) else (
    echo [WARN] Ollama chua cai - Chi dung Gemma 2B
    echo [INFO] Chay SETUP_OLLAMA.bat de cai Qwen2
)

echo.
echo [2/4] Kiem tra Gemma 2B (backup)...

REM Kiem tra model Gemma
if not exist "models\gemma-2-2b-it-Q4_K_M.gguf" (
    echo [WARN] Gemma 2B chua co - Chi dung Qwen2
) else (
    echo [OK] Gemma 2B co san
    
    REM Kiem tra llama-server.exe
    if not exist "llama.cpp\llama-server.exe" (
        echo [WARN] llama-server.exe chua co
    ) else (
        REM Kiem tra server da chay chua
        tasklist /FI "IMAGENAME eq llama-server.exe" 2>NUL | find /I /N "llama-server.exe">NUL
        if %errorlevel% == 1 (
            echo [INFO] Gemma backup chua chay
        ) else (
            echo [OK] Gemma backup dang chay
        )
    )
)

echo.
echo [3/4] Kiem tra AI files...
if exist "ai_assistant.py" (
    echo [OK] AIAssistant OK
) else (
    echo [WARN] AIAssistant chua co
)

if exist "ai\simple_ai.py" (
    echo [OK] SimpleAI OK
) else (
    echo [WARN] SimpleAI chua co
)

if exist "ai\db_queries.json" (
    echo [OK] DB queries OK
) else (
    echo [WARN] DB queries chua co
)

echo.
echo [4/4] Khoi dong app...
echo.

REM Chay app
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe start.py
) else (
    python start.py
)

echo.
echo ========================================
echo   APP DA DONG
echo ========================================
echo.
echo AI Hybrid status:
echo   - Qwen2-1.5B: 0.5-5s response
echo   - Gemma 2B: 5-10s backup
echo   - DB cache: 5 phut TTL
echo.
pause
