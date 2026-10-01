@echo off

call "%~dp0CLEAN_EXISTING_PCYBI.bat"
if errorlevel 1 exit /b 1

setlocal
cd /d "%~dp0"
call "%~dp0BUILD_AND_INSTALL_FINAL.bat"
exit /b %errorlevel%
