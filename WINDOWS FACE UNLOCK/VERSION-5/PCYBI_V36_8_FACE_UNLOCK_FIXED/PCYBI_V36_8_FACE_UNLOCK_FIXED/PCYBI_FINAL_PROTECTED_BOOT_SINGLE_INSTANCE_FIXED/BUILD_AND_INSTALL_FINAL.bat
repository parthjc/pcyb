@echo off

setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title PCYBI V36 // ALL-IN-ONE BUILD + GUIDED INSTALL
net session >nul 2>&1 || (powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs" & exit /b 0)

echo ============================================================
echo PCYBI FINAL - ONE STABLE RELEASE + GUIDED SETUP
echo ============================================================
echo.
where py >nul 2>&1 || goto FAIL
py -3.13 -c "import sys; print('Python:',sys.version)" || goto FAIL
py -3.13 -m pip install --only-binary=:all: "numpy==2.1.3" "pyinstaller==6.22.3" "pywinauto==0.6.9" "pywin32==311" "opencv-contrib-python==4.13.0.92" "cryptography>=44,<47" >nul || goto FAIL
py -3.13 -m py_compile PCYBI_FACE_SETUP.py PCYBI_EVENT_MONITOR.py PCYBI_LOCKSCREEN.py PCYBI_SECURITY_CONSOLE.py PCYBI_INTEGRITY_CHECK.py PCYBI_WATCHDOG_SERVICE.py PCYBI_DIAGNOSTICS.py PCYBI_CONTROL_CENTER.py PCYBI_BACKUP.py PCYBI_HEALTH_CHECK.py PCYBI_ADVANCED_CONTROL_CENTER.py PCYBI_ALL_IN_ONE.py PCYBI_FINAL_TEST.py common.py || goto FAIL
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if not exist data mkdir data
py -3.13 -c "import cv2,shutil; shutil.copy2(cv2.data.haarcascades+'haarcascade_frontalface_default.xml','data\\haarcascade_frontalface_default.xml'); shutil.copy2(cv2.data.haarcascades+'haarcascade_eye.xml','data\\haarcascade_eye.xml')" || goto FAIL

echo [1/5] Building FACE SETUP...
py -3.13 -m PyInstaller --noconfirm --clean --onefile --windowed --name PCYBI_FACE_SETUP --add-data "data\haarcascade_frontalface_default.xml;data" --add-data "data\haarcascade_eye.xml;data" --add-data "common.py;." --collect-submodules cv2 --collect-submodules pywinauto --collect-submodules comtypes --hidden-import cv2.face PCYBI_FACE_SETUP.py || goto FAIL

echo [2/5] Building real Python WATCHDOG SERVICE (SCM dispatcher hotfix)...
py -3.13 -m PyInstaller --noconfirm --clean --onefile --name PCYBI_WATCHDOG_SERVICE --hidden-import win32serviceutil --hidden-import win32service --hidden-import win32event --hidden-import win32ts --hidden-import win32security --hidden-import win32process --hidden-import win32profile --hidden-import win32con --hidden-import servicemanager --hidden-import win32timezone PCYBI_WATCHDOG_SERVICE.py || goto FAIL

echo [3/5] Building EVENT MONITOR + LOCKSCREEN...
py -3.13 -m PyInstaller --noconfirm --clean --onefile --windowed --name PCYBI_EVENT_MONITOR PCYBI_EVENT_MONITOR.py || goto FAIL
py -3.13 -m PyInstaller --noconfirm --clean --onefile --windowed --name PCYBI_LOCKSCREEN --add-data "data\haarcascade_frontalface_default.xml;data" --add-data "data\haarcascade_eye.xml;data" --add-data "common.py;." --collect-submodules cv2 --collect-submodules pywinauto --collect-submodules comtypes --hidden-import cv2.face PCYBI_LOCKSCREEN.py || goto FAIL

echo [4/5] Building ALL SECURITY COMPONENTS...
py -3.13 -m PyInstaller --noconfirm --clean --onefile --windowed --name PCYBI_SECURITY_CONSOLE PCYBI_SECURITY_CONSOLE.py || goto FAIL
py -3.13 -m PyInstaller --noconfirm --clean --onefile --name PCYBI_INTEGRITY_CHECK PCYBI_INTEGRITY_CHECK.py || goto FAIL
py -3.13 -m PyInstaller --noconfirm --clean --onefile --windowed --name PCYBI_DIAGNOSTICS PCYBI_DIAGNOSTICS.py || goto FAIL
py -3.13 -m PyInstaller --noconfirm --clean --onefile --windowed --name PCYBI_CONTROL_CENTER PCYBI_CONTROL_CENTER.py || goto FAIL
py -3.13 -m PyInstaller --noconfirm --clean --onefile --name PCYBI_HEALTH_CHECK PCYBI_HEALTH_CHECK.py || goto FAIL
py -3.13 -m PyInstaller --noconfirm --clean --onefile --windowed --name PCYBI_ALL_IN_ONE PCYBI_ALL_IN_ONE.py || goto FAIL
py -3.13 -m PyInstaller --noconfirm --clean --onefile --name PCYBI_FINAL_TEST PCYBI_FINAL_TEST.py || goto FAIL
py -3.13 -m PyInstaller --noconfirm --clean --onefile --windowed --name PCYBI_ADVANCED_CONTROL_CENTER PCYBI_ADVANCED_CONTROL_CENTER.py || goto FAIL
py -3.13 -m PyInstaller --noconfirm --clean --onefile --name PCYBI_BACKUP PCYBI_BACKUP.py || goto FAIL
for %%F in (PCYBI_FACE_SETUP.exe PCYBI_WATCHDOG_SERVICE.exe PCYBI_EVENT_MONITOR.exe PCYBI_LOCKSCREEN.exe PCYBI_SECURITY_CONSOLE.exe PCYBI_INTEGRITY_CHECK.exe PCYBI_DIAGNOSTICS.exe PCYBI_CONTROL_CENTER.exe PCYBI_BACKUP.exe PCYBI_HEALTH_CHECK.exe PCYBI_ADVANCED_CONTROL_CENTER.exe PCYBI_ALL_IN_ONE.exe PCYBI_FINAL_TEST.exe) do if not exist "dist\%%F" (echo ERROR missing %%F&goto FAIL)

echo [5/5] Installing V36 and starting guided setup...
call "%~dp0INSTALL_PCYBI_FINAL.bat"
if errorlevel 1 goto FAIL
call "%~dp0PCYBI_AUTO_REPAIR.bat"
if errorlevel 1 goto FAIL
echo PCYBI automatic build + install + service verification COMPLETE.
exit /b 0
:FAIL
echo ============================================================
echo PCYBI FINAL BUILD/INSTALL FAILED
echo ============================================================
pause
exit /b 1
