@echo off
setlocal
cd /d "%~dp0"
set "ROOT=%ProgramData%\PCYBI\System"
if exist "%ROOT%\PCYBI_FINAL_TEST.exe" (
  "%ROOT%\PCYBI_FINAL_TEST.exe"
  exit /b %errorlevel%
)
if exist "%ROOT%\PCYBI_DIAGNOSTICS.exe" "%ROOT%\PCYBI_DIAGNOSTICS.exe"
if exist "%ROOT%\PCYBI_HEALTH_CHECK.exe" "%ROOT%\PCYBI_HEALTH_CHECK.exe"
sc.exe query PCYBIWatchdog
pause
