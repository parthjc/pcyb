@echo off
setlocal
net session >nul 2>&1 || (powershell.exe -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs" & exit /b 0)
set "ROOT=%ProgramData%\ZYNTRASEC\System"
echo ============================================================
echo ZYNTRASEC V35 // ADVANCED SERVICE REPAIR
echo ============================================================
sc.exe stop ZYNTRASECWatchdog >nul 2>&1
for /l %%N in (1,1,15) do (
  sc.exe query ZYNTRASECWatchdog | findstr /I "STOPPED" >nul && goto stopped
  timeout /t 1 /nobreak >nul
)
:stopped
sc.exe config ZYNTRASECWatchdog start= auto >nul
sc.exe failure ZYNTRASECWatchdog reset=86400 actions=restart/5000/restart/10000/restart/30000 >nul
sc.exe failureflag ZYNTRASECWatchdog 1 >nul
if exist "%ROOT%\ZYNTRASEC_WATCHDOG_SERVICE.exe" (
  sc.exe start ZYNTRASECWatchdog
) else (
  echo Missing watchdog binary: %ROOT%\ZYNTRASEC_WATCHDOG_SERVICE.exe
  pause
  exit /b 2
)
sc.exe query ZYNTRASECWatchdog
if exist "%ROOT%\ZYNTRASEC_HEALTH_CHECK.exe" "%ROOT%\ZYNTRASEC_HEALTH_CHECK.exe"
echo.
echo Repair completed. If the service remains STOPPED, open the query output above.
pause
