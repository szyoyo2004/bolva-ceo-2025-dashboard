@echo off
chcp 65001 >nul
echo ========================================================
echo   BOLVA CEO Strategic Console - Auto Launcher
echo ========================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Please install Python first.
    pause
    exit /b
)

echo [INFO] Checking dependencies...
python -c "import streamlit" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] Streamlit not found. Installing dependencies...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b
    )
    echo [INFO] Dependencies installed successfully.
) else (
    echo [INFO] Dependencies ready.
)

echo.
echo [INFO] Starting Dashboard...
echo [INFO] Please wait for the browser to open...
echo.

:: Run using python -m to avoid PATH issues
python -m streamlit run app3.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Application crashed. See error message above.
)
pause
