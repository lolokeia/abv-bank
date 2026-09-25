@echo off
chcp 65001 >nul
echo   Установка библиотек для ABV-BANK
echo.

pip install -r requirements.txt

echo   Все библиотеки установлены!
pause