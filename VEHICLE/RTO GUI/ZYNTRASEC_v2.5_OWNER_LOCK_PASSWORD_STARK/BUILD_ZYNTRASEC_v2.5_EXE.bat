@echo off
setlocal
title ZYNTRASEC v2.5 EXE BUILDER
cd /d "%~dp0"

echo ============================================================
echo        ZYNTRASEC v2.5 ALL VEHICLES EXE BUILDER
echo ============================================================
echo.

where py >nul 2>&1
if %errorlevel%==0 (
  set "PY=py"
) else (
  set "PY=python"
)

echo [1/4] Checking Python...
%PY% --version
if errorlevel 1 (
  echo Python not found. Install Python 3 and enable PATH.
  pause
  exit /b 1
)

echo.
echo [2/4] Installing PyInstaller...
%PY% -m pip install --upgrade pyinstaller
if errorlevel 1 (
  echo PyInstaller installation failed.
  pause
  exit /b 1
)

echo.
echo [3/4] Building EXE...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist ZYNTRASEC_v2.5.spec del /q ZYNTRASEC_v2.5.spec

%PY% -m PyInstaller --clean --noconfirm --onefile --console --name ZYNTRASEC_v2.5 "ZYNTRASEC_v2.5_ALL_VEHICLES_IMAGE_ENGINE.py"

if errorlevel 1 (
  echo.
  echo BUILD FAILED.
  pause
  exit /b 1
)

echo.
echo [4/4] DONE
echo.
echo EXE created at:
echo %~dp0dist\ZYNTRASEC_v2.5.exe
echo.
pause
