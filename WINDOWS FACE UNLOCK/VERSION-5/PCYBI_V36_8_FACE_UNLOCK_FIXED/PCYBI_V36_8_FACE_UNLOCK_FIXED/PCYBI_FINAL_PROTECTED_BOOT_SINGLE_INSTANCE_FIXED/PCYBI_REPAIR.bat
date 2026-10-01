@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title PCYBI // REPAIR
net session >nul 2>&1 || (powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs" & exit /b 0)
set "ROOT=%ProgramData%\PCYBI\System"
set "SERVICE=PCYBIWatchdog"
echo ============================================================
echo PCYBI ALL-IN-ONE REPAIR
echo ============================================================
sc.exe stop "%SERVICE%" >nul 2>&1
for %%P in (PCYBI_EVENT_MONITOR.exe PCYBI_LOCKSCREEN.exe PCYBI_SECURITY_CONSOLE.exe) do taskkill /F /IM "%%P" >nul 2>&1
if not exist "%ROOT%\PCYBI_WATCHDOG_SERVICE.exe" (echo Missing watchdog executable.& exit /b 2)
sc.exe query "%SERVICE%" >nul 2>&1 || sc.exe create "%SERVICE%" binPath= "\"%ROOT%\PCYBI_WATCHDOG_SERVICE.exe\"" start= auto type= own obj= LocalSystem DisplayName= "PCYBI Security Watchdog"
sc.exe config "%SERVICE%" start= auto >nul
sc.exe description "%SERVICE%" "PCYBI protected boot watchdog service" >nul
sc.exe failure "%SERVICE%" reset=86400 actions=restart/5000/restart/10000/restart/30000 >nul
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$u=[Security.Principal.WindowsIdentity]::GetCurrent().Name; $a=New-ScheduledTaskAction -Execute '%ROOT%\PCYBI_EVENT_MONITOR.exe'; $p=New-ScheduledTaskPrincipal -UserId $u -LogonType Interactive -RunLevel Highest; $t=New-ScheduledTaskTrigger -AtLogOn; Register-ScheduledTask -TaskName 'PCYBI User Event Monitor' -Action $a -Principal $p -Trigger $t -Force | Out-Null"
sc.exe start "%SERVICE%" >nul 2>&1
"%ROOT%\PCYBI_INTEGRITY_CHECK.exe"
"%ROOT%\PCYBI_DIAGNOSTICS.exe"
echo.
echo Repair complete. Check diagnostics_latest.json for details.
pause
