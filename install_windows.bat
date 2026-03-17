@echo off
REM Rate Edge v5.1 - Windows Installation Script
echo ============================================================
echo    Rate Edge v5.1 - Professional IRS Swap Analytics
echo    Installation Script for Windows
echo ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] Python found! Checking version...
python --version

echo.
echo [2/3] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [3/3] Verifying installation...
python -c "import pandas; import matplotlib; import flask; print('All packages installed successfully!')"
if errorlevel 1 (
    echo [ERROR] Package verification failed
    pause
    exit /b 1
)

echo.
echo ============================================================
echo    Installation Complete!
echo ============================================================
echo.
echo You can now launch Rate Edge:
echo.
echo   Desktop App:  python launch.py
echo   Web App:      python web_app.py
echo.
echo Check QUICKSTART.md for a 2-minute tutorial!
echo.
pause
