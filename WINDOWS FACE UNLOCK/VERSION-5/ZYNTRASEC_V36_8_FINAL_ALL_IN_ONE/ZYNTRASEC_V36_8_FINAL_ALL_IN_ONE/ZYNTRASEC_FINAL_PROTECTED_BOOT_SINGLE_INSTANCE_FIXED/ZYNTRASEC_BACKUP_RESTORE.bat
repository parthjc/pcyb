@echo off
setlocal
cd /d "%~dp0"
set "ROOT=%ProgramData%\ZYNTRASEC\System"
if not exist "%ROOT%\ZYNTRASEC_BACKUP.exe" (echo ZYNTRASEC backup tool is not installed.& pause & exit /b 2)
if "%~1"=="" (
  "%ROOT%\ZYNTRASEC_BACKUP.exe"
) else (
  "%ROOT%\ZYNTRASEC_BACKUP.exe" restore "%~1"
)
pause
