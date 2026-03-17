@echo off
cls
echo ==============================================================================
echo   Rate Edge v7.2 - BlueGamma Data Import
echo ==============================================================================
echo.
echo This will import all your AUD and NZD swap and OIS data.
echo.
echo Make sure your CSV files are in:
echo C:\Users\willp\IRS_DATA_Manager\BlueGamma\
echo.
pause
echo.
echo Starting import...
echo.

python import_bluegamma.py

echo.
echo ==============================================================================
echo   Import Complete!
echo ==============================================================================
echo.
pause
