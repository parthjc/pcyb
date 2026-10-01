@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
net session >nul 2>&1 || (powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs" & exit /b 0)
set "ROOT=%ProgramData%\PCYBI\System"
set "SERVICE=PCYBIWatchdog"
set "TASK=PCYBI User Event Monitor"
set "LOCKTASK=PCYBI Lock Screen"
set "EXE=%ROOT%\PCYBI_WATCHDOG_SERVICE.exe"

echo ============================================================
echo PCYBI // AUTOMATIC SERVICE REPAIR
echo ============================================================

if not exist "%EXE%" (
  echo ERROR: Watchdog executable not found: %EXE%
  exit /b 10
)

sc.exe stop "%SERVICE%" >nul 2>&1
for /L %%N in (1,1,15) do (
  sc.exe query "%SERVICE%" | findstr /I "STOPPED" >nul 2>&1 && goto STOPPED
  timeout /t 1 /nobreak >nul
)
:STOPPED

sc.exe delete "%SERVICE%" >nul 2>&1
for /L %%N in (1,1,10) do (
  sc.exe query "%SERVICE%" >nul 2>&1 || goto DELETED
  timeout /t 1 /nobreak >nul
)
:DELETED

sc.exe create "%SERVICE%" binPath= "\"%EXE%\"" start= delayed-auto type= own obj= LocalSystem DisplayName= "PCYBI Security Watchdog" || exit /b 20
sc.exe description "%SERVICE%" "PCYBI protected boot watchdog service" >nul
sc.exe failure "%SERVICE%" reset=86400 actions=restart/5000/restart/10000/restart/30000 >nul
sc.exe failureflag "%SERVICE%" 1 >nul

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $u=[Security.Principal.WindowsIdentity]::GetCurrent().Name; $a=New-ScheduledTaskAction -Execute '%ROOT%\PCYBI_EVENT_MONITOR.exe'; $p=New-ScheduledTaskPrincipal -UserId $u -LogonType Interactive -RunLevel Highest; $t=New-ScheduledTaskTrigger -AtLogOn; Register-ScheduledTask -TaskName '%TASK%' -Action $a -Principal $p -Trigger $t -Force | Out-Null" || exit /b 30

sc.exe start "%SERVICE%" >nul 2>&1
for /L %%N in (1,1,30) do (
  sc.exe query "%SERVICE%" | findstr /I "RUNNING" >nul 2>&1 && goto OK
  timeout /t 1 /nobreak >nul
)

echo ERROR: Watchdog did not reach RUNNING.
sc.exe query "%SERVICE%"
exit /b 40
:OK
sc.exe qc "%SERVICE%"
echo.
echo Logon monitor task : READY
echo Logon lock task    : READY
echo PCYBI automatic repair COMPLETE.
exit /b 0
