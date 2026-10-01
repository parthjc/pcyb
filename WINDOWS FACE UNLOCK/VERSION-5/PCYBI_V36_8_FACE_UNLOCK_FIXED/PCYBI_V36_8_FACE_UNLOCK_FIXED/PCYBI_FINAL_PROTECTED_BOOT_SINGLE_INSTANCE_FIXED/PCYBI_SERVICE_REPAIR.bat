@echo off
setlocal EnableExtensions
cd /d "%~dp0"
net session >nul 2>&1 || (powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs" & exit /b 0)
set "ROOT=%ProgramData%\PCYBI\System"
set "SERVICE=PCYBIWatchdog"
echo ============================================================
echo PCYBI SERVICE REPAIR - V34.1
echo ============================================================
echo.
sc.exe stop "%SERVICE%" >nul 2>&1
timeout /t 2 /nobreak >nul
if exist "%ROOT%\PCYBI_WATCHDOG_SERVICE.exe" copy /y "%ROOT%\PCYBI_WATCHDOG_SERVICE.exe" "%ROOT%\PCYBI_WATCHDOG_SERVICE.exe.bak" >nul
sc.exe config "%SERVICE%" start= auto >nul 2>&1
sc.exe failure "%SERVICE%" reset=86400 actions=restart/5000/restart/10000/restart/30000 >nul 2>&1
sc.exe start "%SERVICE%"
if errorlevel 1 goto FAIL
for /L %%N in (1,1,30) do (
  for /F "tokens=4" %%S in ('sc.exe query "%SERVICE%" ^| findstr /I "STATE"') do if /I "%%S"=="RUNNING" goto OK
  timeout /t 1 /nobreak >nul
)
:FAIL
echo.
echo Service did not reach RUNNING.
sc.exe query "%SERVICE%"
echo.
echo If this is still 1053, run:
echo   sc.exe queryex %SERVICE%
echo   type "%ROOT%\watchdog.log"
pause
exit /b 1
:OK
echo.
echo PCYBIWatchdog is RUNNING.
echo.
pause
exit /b 0
