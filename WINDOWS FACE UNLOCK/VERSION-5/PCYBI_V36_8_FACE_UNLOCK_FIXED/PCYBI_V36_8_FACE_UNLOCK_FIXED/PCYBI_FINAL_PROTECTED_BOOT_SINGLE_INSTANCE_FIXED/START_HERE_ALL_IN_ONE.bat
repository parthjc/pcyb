@echo off
setlocal
cd /d "%~dp0"
net session >nul 2>&1 || (powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs" & exit /b 0)
call "%~dp0START_HERE.bat"
