@echo off
chcp 65001 >nul
echo   Downloading libs for ABV-BANK
echo.

pip install -r requirements.txt

echo   All libs installed!
pause