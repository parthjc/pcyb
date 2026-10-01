@echo off
setlocal
cd /d "%~dp0"
echo ================================================
echo ZYNTRASEC - EXE BUILD
 echo ================================================
where py >nul 2>&1 || (echo Python not found. Install Python 3.13 and retry.&pause&exit /b 1)
py -m pip install --upgrade pyinstaller
if errorlevel 1 (echo PyInstaller install failed.&pause&exit /b 1)
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
py -m PyInstaller --noconfirm --clean --onefile --windowed --name ZYNTRASEC ZYNTRASEC.py
if errorlevel 1 (echo EXE BUILD FAILED.&pause&exit /b 1)
echo.
echo BUILD COMPLETE:
echo %cd%\dist\ZYNTRASEC.exe
pause
