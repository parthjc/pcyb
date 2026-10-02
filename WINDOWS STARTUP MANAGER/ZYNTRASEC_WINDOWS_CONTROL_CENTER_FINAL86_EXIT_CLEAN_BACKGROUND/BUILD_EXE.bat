@echo off
setlocal
cd /d "%~dp0"
title ZYNTRASEC EXE BUILDER
color 0A

echo ================================================================
echo ZYNTRASEC // WINDOWS CONTROL CENTER - EXE BUILDER
echo ================================================================
echo.

where py >nul 2>&1
if %errorlevel%==0 (
  set "PY=py"
) else (
  where python >nul 2>&1
  if %errorlevel%==0 (
    set "PY=python"
  ) else (
    echo [ERROR] Python was not found.
    echo Install Python 3.11+ and run this file again.
    pause
    exit /b 1
  )
)

%PY% -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
  echo [INFO] PyInstaller is not installed. Installing...
  %PY% -m pip install pyinstaller
  if errorlevel 1 (
    echo [ERROR] PyInstaller installation failed.
    echo Check your internet connection or install it manually with:
    echo   %PY% -m pip install pyinstaller
    pause
    exit /b 1
  )
)

echo [INFO] Building ZYNTRASEC EXE...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist ZYNTRASEC_WINDOWS_CONTROL_CENTER.spec del /q ZYNTRASEC_WINDOWS_CONTROL_CENTER.spec

%PY% -m PyInstaller --noconfirm --clean --onedir --windowed --name ZYNTRASEC_WINDOWS_CONTROL_CENTER main.py
if errorlevel 1 (
  echo.
  echo [ERROR] EXE build failed.
  pause
  exit /b 1
)

if exist config.json copy /y config.json "dist\ZYNTRASEC_WINDOWS_CONTROL_CENTER\config.json" >nul
if exist README.txt copy /y README.txt "dist\ZYNTRASEC_WINDOWS_CONTROL_CENTER\README.txt" >nul

echo.
echo ================================================================
echo BUILD COMPLETE
 echo EXE: dist\ZYNTRASEC_WINDOWS_CONTROL_CENTER\ZYNTRASEC_WINDOWS_CONTROL_CENTER.exe
echo ================================================================
echo.
start "" "dist\ZYNTRASEC_WINDOWS_CONTROL_CENTER"
pause
