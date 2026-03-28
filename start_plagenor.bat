@echo off
:: ============================================================
:: PLAGENOR 4.0 — Windows Startup Script
:: Works both for manual launch and as an NSSM service wrapper
:: ============================================================

setlocal EnableDelayedExpansion

:: --- Resolve script directory (works from any CWD, including NSSM) ---
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: --- Check venv exists ---
if not exist ".\venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found at .\venv\
    echo         Run: python -m venv venv   then   venv\Scripts\activate   then   pip install -r requirements.txt
    exit /b 1
)

:: --- Activate the virtual environment ---
call ".\venv\Scripts\activate.bat"

:: --- Load environment variables from .env if it exists ---
if exist ".env" (
    echo [INFO] Loading environment variables from .env ...
    for /f "usebackq tokens=1,* delims==" %%A in (`findstr /v "^#" .env`) do (
        set "%%A=%%B"
    )
) else (
    echo [WARN] No .env file found. Using system environment variables only.
    echo        Copy .env.example to .env and configure before production use.
)

:: --- Ensure logs directory exists ---
if not exist "logs" mkdir logs

:: --- Launch Streamlit ---
echo [INFO] Starting PLAGENOR 4.0 on http://0.0.0.0:8501 ...
python -m streamlit run app.py ^
    --server.address=0.0.0.0 ^
    --server.port=8501 ^
    --server.headless=true ^
    --browser.gatherUsageStats=false

:: --- Capture exit code ---
set EXIT_CODE=%ERRORLEVEL%
if %EXIT_CODE% neq 0 (
    echo [ERROR] Streamlit exited with code %EXIT_CODE%
)

endlocal
exit /b %EXIT_CODE%
