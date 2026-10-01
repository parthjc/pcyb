@echo off
setlocal
net session >nul 2>&1 || (powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs" & exit /b 0)
set "ROOT=%ProgramData%\ZYNTRASEC\System"
echo ============================================================
echo ZYNTRASEC FINAL VERIFY
 echo ============================================================
echo [SERVICE]
sc.exe query ZYNTRASECWatchdog
sc.exe qc ZYNTRASECWatchdog

echo.
echo [RECOVERY TASKS]
schtasks.exe /query /tn "ZYNTRASEC Logon Service Recovery" /fo LIST 2>nul
schtasks.exe /query /tn "ZYNTRASEC User Event Monitor" /fo LIST 2>nul

echo.
echo [PROCESSES]
tasklist.exe | findstr /I "ZYNTRASEC" || echo No ZYNTRASEC process found.

echo.
echo [SINGLE INSTANCE COUNTS]
powershell.exe -NoProfile -Command "$m=@(Get-Process -Name ZYNTRASEC_EVENT_MONITOR -ErrorAction SilentlyContinue); 'EventMonitorCount=' + $m.Count; $a=@(Get-Process -Name ZYNTRASEC_WATCHDOG_AGENT -ErrorAction SilentlyContinue); 'WatchdogAgentCount=' + $a.Count; $s=(sc.exe query ZYNTRASECWatchdog | Select-String 'STATE'); 'ServiceState=' + $s.Line"

echo.
echo [INSTALLED FILES]
for %%F in (ZYNTRASEC_WATCHDOG_SERVICE.exe ZYNTRASEC_EVENT_MONITOR.exe ZYNTRASEC_LOCKSCREEN.exe ZYNTRASEC_FACE_SETUP.exe ZYNTRASEC_SECURITY_CONSOLE.exe ZYNTRASEC_INTEGRITY_CHECK.exe) do if exist "%ROOT%\%%F" (echo OK %%F) else (echo MISSING %%F)

echo.
echo [RECENT SERVICE ERRORS]
powershell.exe -NoProfile -Command "Get-WinEvent -FilterHashtable @{LogName='System';Id=7000,7009,7031,7034} -MaxEvents 10 -ErrorAction SilentlyContinue | Format-List TimeCreated,Id,ProviderName,Message"
pause
