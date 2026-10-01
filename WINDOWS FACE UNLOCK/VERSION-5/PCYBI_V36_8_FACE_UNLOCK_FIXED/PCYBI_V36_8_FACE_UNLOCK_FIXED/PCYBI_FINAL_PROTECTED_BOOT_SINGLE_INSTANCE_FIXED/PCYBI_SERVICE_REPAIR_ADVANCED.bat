@echo off
setlocal
net session >nul 2>&1 || (powershell.exe -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs" & exit /b 0)
set "ROOT=%ProgramData%\PCYBI\System"
echo ============================================================
echo PCYBI V35 // ADVANCED SERVICE REPAIR
echo ============================================================
sc.exe stop PCYBIWatchdog >nul 2>&1
for /l %%N in (1,1,15) do (
  sc.exe query PCYBIWatchdog | findstr /I "STOPPED" >nul && goto stopped
  timeout /t 1 /nobreak >nul
)
:stopped
sc.exe config PCYBIWatchdog start= auto >nul
sc.exe failure PCYBIWatchdog reset=86400 actions=restart/5000/restart/10000/restart/30000 >nul
sc.exe failureflag PCYBIWatchdog 1 >nul
if exist "%ROOT%\PCYBI_WATCHDOG_SERVICE.exe" (
  sc.exe start PCYBIWatchdog
) else (
  echo Missing watchdog binary: %ROOT%\PCYBI_WATCHDOG_SERVICE.exe
  pause
  exit /b 2
)
sc.exe query PCYBIWatchdog
if exist "%ROOT%\PCYBI_HEALTH_CHECK.exe" "%ROOT%\PCYBI_HEALTH_CHECK.exe"
echo.
echo Repair completed. If the service remains STOPPED, open the query output above.
pause
