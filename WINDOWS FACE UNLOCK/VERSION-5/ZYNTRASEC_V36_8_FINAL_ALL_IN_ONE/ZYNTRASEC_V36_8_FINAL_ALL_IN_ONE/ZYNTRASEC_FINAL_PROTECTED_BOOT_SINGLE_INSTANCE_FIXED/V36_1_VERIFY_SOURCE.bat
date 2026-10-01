@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1 || (echo ERROR: Python launcher not found.&exit /b 1)
py -3.13 -m py_compile *.py || (echo ERROR: Python syntax check failed.&exit /b 2)
echo PASS: All ZYNTRASEC Python source files compile successfully.
exit /b 0
