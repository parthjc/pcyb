@echo off
setlocal
net session >nul 2>&1 || (powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs" & exit /b 0)
set "ROOT=%ProgramData%\PCYBI\System"
echo ============================================================
echo PCYBI FINAL VERIFY
 echo ============================================================
echo [SERVICE]
sc.exe query PCYBIWatchdog
sc.exe qc PCYBIWatchdog

echo.
echo [RECOVERY TASKS]
schtasks.exe /query /tn "PCYBI Logon Service Recovery" /fo LIST 2>nul
schtasks.exe /query /tn "PCYBI User Event Monitor" /fo LIST 2>nul

echo.
echo [PROCESSES]
tasklist.exe | findstr /I "PCYBI" || echo No PCYBI process found.

echo.
echo [SINGLE INSTANCE COUNTS]
powershell.exe -NoProfile -Command "$m=@(Get-Process -Name PCYBI_EVENT_MONITOR -ErrorAction SilentlyContinue); 'EventMonitorCount=' + $m.Count; $a=@(Get-Process -Name PCYBI_WATCHDOG_AGENT -ErrorAction SilentlyContinue); 'WatchdogAgentCount=' + $a.Count; $s=(sc.exe query PCYBIWatchdog | Select-String 'STATE'); 'ServiceState=' + $s.Line"

echo.
echo [INSTALLED FILES]
for %%F in (PCYBI_WATCHDOG_SERVICE.exe PCYBI_EVENT_MONITOR.exe PCYBI_LOCKSCREEN.exe PCYBI_FACE_SETUP.exe PCYBI_SECURITY_CONSOLE.exe PCYBI_INTEGRITY_CHECK.exe) do if exist "%ROOT%\%%F" (echo OK %%F) else (echo MISSING %%F)

echo.
echo [RECENT SERVICE ERRORS]
powershell.exe -NoProfile -Command "Get-WinEvent -FilterHashtable @{LogName='System';Id=7000,7009,7031,7034} -MaxEvents 10 -ErrorAction SilentlyContinue | Format-List TimeCreated,Id,ProviderName,Message"
pause
