@echo off
title Spot The Difference Studio - KDP Book Creator
cls
color 0B
echo.
echo ========================================================
echo    SPOT THE DIFFERENCE STUDIO - KDP BOOK CREATOR
echo ========================================================
echo.
echo [*] Starting Studio server...
echo [*] Opening your browser at http://127.0.0.1:5000 ...
echo.

start "" /b cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:5000"

where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    py app.py
) else (
    python app.py
)

if %ERRORLEVEL% neq 0 (
    color 0C
    echo.
    echo [!] An error occurred while running the studio.
    echo.
    pause
)
