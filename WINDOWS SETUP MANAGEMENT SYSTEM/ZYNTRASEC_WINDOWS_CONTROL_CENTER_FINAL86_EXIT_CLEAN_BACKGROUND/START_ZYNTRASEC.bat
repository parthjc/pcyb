@echo off
setlocal
cd /d "%~dp0"
title ZYNTRASEC // WINDOWS CONTROL CENTER

:: Auto-elevate because partition operations require Administrator rights.
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found in PATH.
    echo Install Python 3.11+ and enable "Add Python to PATH".
    pause
    exit /b 1
)

python main.py
set "RC=%errorlevel%"
if not "%RC%"=="0" echo [ERROR] ZYNTRASEC exited with code %RC%.
pause
exit /b %RC%
