@echo off
setlocal
cd /d "%~dp0"
title ZYNTRASEC V33 // SOURCE VERIFY
where py >nul 2>&1 || (echo Python launcher not found.& exit /b 1)
py -3.13 -m py_compile common.py ZYNTRASEC_FACE_SETUP.py ZYNTRASEC_EVENT_MONITOR.py ZYNTRASEC_LOCKSCREEN.py ZYNTRASEC_SECURITY_CONSOLE.py ZYNTRASEC_INTEGRITY_CHECK.py ZYNTRASEC_WATCHDOG_SERVICE.py
if errorlevel 1 (echo SOURCE COMPILE FAILED.& exit /b 2)
echo.
echo ZYNTRASEC V33 source verification: PASS
echo Python syntax: PASS
echo Files are ready for the Windows build step.
exit /b 0
