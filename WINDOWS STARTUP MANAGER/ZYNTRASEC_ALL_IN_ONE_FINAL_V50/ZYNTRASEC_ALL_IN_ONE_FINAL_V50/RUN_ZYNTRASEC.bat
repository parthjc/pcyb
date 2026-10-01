@echo off
setlocal
cd /d "%~dp0"
where pythonw.exe >nul 2>&1
if errorlevel 1 (python "%~dp0ZYNTRASEC.py" & exit /b)
start "" /b pythonw.exe "%~dp0ZYNTRASEC.py"
