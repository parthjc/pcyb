@echo off
setlocal
cd /d "%~dp0"
set "ROOT=%ProgramData%\ZYNTRASEC\System"
if exist "%ROOT%\ZYNTRASEC_FINAL_TEST.exe" (
  "%ROOT%\ZYNTRASEC_FINAL_TEST.exe"
  exit /b %errorlevel%
)
if exist "%ROOT%\ZYNTRASEC_DIAGNOSTICS.exe" "%ROOT%\ZYNTRASEC_DIAGNOSTICS.exe"
if exist "%ROOT%\ZYNTRASEC_HEALTH_CHECK.exe" "%ROOT%\ZYNTRASEC_HEALTH_CHECK.exe"
sc.exe query ZYNTRASECWatchdog
pause
