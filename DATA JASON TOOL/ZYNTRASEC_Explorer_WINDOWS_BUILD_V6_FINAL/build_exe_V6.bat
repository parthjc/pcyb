@echo off
setlocal EnableExtensions
title ZYNTRASEC Explorer - Windows EXE Builder

echo.
echo ============================================================
echo   ZYNTRASEC Explorer - Standalone Windows EXE Builder
echo ============================================================
echo.

cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    set "PY=py"
) else (
    where python >nul 2>nul
    if %errorlevel%==0 (
        set "PY=python"
    ) else (
        echo [1/4] Python not found. Trying Windows Package Manager...
        where winget >nul 2>nul
        if not %errorlevel%==0 (
            echo.
            echo ERROR: Python and winget are not available.
            echo Install Python 3.13 on this BUILD PC, then run this file again.
            echo The FINAL EXE itself will NOT require Python.
            pause
            exit /b 1
        )
        winget install --id Python.Python.3.13 -e --scope user --accept-source-agreements --accept-package-agreements
        if not %errorlevel%==0 (
            echo.
            echo ERROR: Python installation failed.
            pause
            exit /b 1
        )
        set "PY=py"
    )
)

echo [2/4] Upgrading pip and installing PyInstaller...
%PY% -m pip install --upgrade pip
if not %errorlevel%==0 (
    echo ERROR: pip setup failed.
    pause
    exit /b 1
)

%PY% -m pip install --upgrade pyinstaller
if not %errorlevel%==0 (
    echo ERROR: PyInstaller installation failed.
    pause
    exit /b 1
)

if not exist "ZYNTRASEC_Explorer_PRO_FINAL_V6.py" (
    echo ERROR: ZYNTRASEC_Explorer_PRO_FINAL_V6.py not found.
    pause
    exit /b 1
)

echo [3/4] Building single-file EXE...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist ZYNTRASEC_Explorer_PRO.spec del /q ZYNTRASEC_Explorer_PRO.spec

%PY% -m PyInstaller ^
  --onefile ^
  --windowed ^
  --clean ^
  --noconfirm ^
  --name ZYNTRASEC_Explorer_PRO ^
  "ZYNTRASEC_Explorer_PRO_FINAL_V6.py"

if not %errorlevel%==0 (
    echo.
    echo ERROR: EXE build failed.
    pause
    exit /b 1
)

echo [4/4] BUILD COMPLETE
echo.
echo Final EXE:
echo   %cd%\dist\ZYNTRASEC_Explorer_PRO.exe
echo.
echo Python is bundled into the EXE.
echo Target Windows PCs do NOT need Python installed.
echo.
pause
endlocal
