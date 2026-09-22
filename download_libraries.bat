@echo off
chcp 65001 >nul
echo ========================================
echo   Установка библиотек для ABV-BANK
echo ========================================
echo.

echo [1/2] Установка bcrypt...
python -m pip install bcrypt
if errorlevel 1 (
    echo ОШИБКА: не удалось установить bcrypt
    pause
    exit /b 1
)
echo.

echo [2/2] Установка cryptography...
python -m pip install cryptography
if errorlevel 1 (
    echo ОШИБКА: не удалось установить cryptography
    pause
    exit /b 1
)
echo.

echo ========================================
echo   Все библиотеки установлены!
echo ========================================
pause