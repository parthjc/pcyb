@echo off
setlocal EnableExtensions
title ZYNTRASEC Explorer V6 - Freeze Fixed
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (set "PY=py") else (set "PY=python")

echo ============================================================
echo   ZYNTRASEC Explorer V6 - FREEZE FIXED BUILD
echo ============================================================
echo.

%PY% -m pip install --upgrade pyinstaller
if errorlevel 1 goto BUILD_FAIL

if not exist "ZYNTRASEC_Explorer_PRO_FINAL_V6_FREEZE_FIXED.py" (
    echo ERROR: source file not found.
    goto BUILD_FAIL
)

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist ZYNTRASEC_Explorer_PRO.spec del /q ZYNTRASEC_Explorer_PRO.spec

%PY% -m PyInstaller --onefile --windowed --clean --noconfirm --name ZYNTRASEC_Explorer_PRO "ZYNTRASEC_Explorer_PRO_FINAL_V6_FREEZE_FIXED.py"
if errorlevel 1 goto BUILD_FAIL

echo.
echo BUILD COMPLETE:
echo %cd%\dist\ZYNTRASEC_Explorer_PRO.exe
echo.
pause
endlocal
exit /b 0

:BUILD_FAIL
echo.
echo BUILD FAILED.
pause
endlocal
exit /b 1
