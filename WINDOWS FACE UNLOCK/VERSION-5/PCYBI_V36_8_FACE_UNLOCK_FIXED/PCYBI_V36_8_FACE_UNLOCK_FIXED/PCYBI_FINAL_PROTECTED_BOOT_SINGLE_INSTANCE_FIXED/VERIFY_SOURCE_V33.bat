@echo off
setlocal
cd /d "%~dp0"
title PCYBI V33 // SOURCE VERIFY
where py >nul 2>&1 || (echo Python launcher not found.& exit /b 1)
py -3.13 -m py_compile common.py PCYBI_FACE_SETUP.py PCYBI_EVENT_MONITOR.py PCYBI_LOCKSCREEN.py PCYBI_SECURITY_CONSOLE.py PCYBI_INTEGRITY_CHECK.py PCYBI_WATCHDOG_SERVICE.py
if errorlevel 1 (echo SOURCE COMPILE FAILED.& exit /b 2)
echo.
echo PCYBI V33 source verification: PASS
echo Python syntax: PASS
echo Files are ready for the Windows build step.
exit /b 0
