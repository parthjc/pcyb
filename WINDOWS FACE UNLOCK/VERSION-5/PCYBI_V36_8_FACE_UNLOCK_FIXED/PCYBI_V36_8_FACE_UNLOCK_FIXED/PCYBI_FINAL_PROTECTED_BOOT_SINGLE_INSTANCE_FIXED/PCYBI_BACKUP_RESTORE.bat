@echo off
setlocal
cd /d "%~dp0"
set "ROOT=%ProgramData%\PCYBI\System"
if not exist "%ROOT%\PCYBI_BACKUP.exe" (echo PCYBI backup tool is not installed.& pause & exit /b 2)
if "%~1"=="" (
  "%ROOT%\PCYBI_BACKUP.exe"
) else (
  "%ROOT%\PCYBI_BACKUP.exe" restore "%~1"
)
pause
