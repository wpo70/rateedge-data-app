@echo off
cls
echo ==============================================================================
echo   Rate Edge v7.2 - Professional Edition
echo   Starting application with table views...
echo ==============================================================================
echo.

python launch.py

if errorlevel 1 (
    echo.
    echo ==============================================================================
    echo   Error starting Rate Edge
    echo   Make sure Python is installed and requirements are met
    echo ==============================================================================
    echo.
    pause
)
