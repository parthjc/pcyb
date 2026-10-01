@echo off
setlocal EnableExtensions
title ZYNTRASEC FINAL - FULL UNINSTALL

:: Require Administrator
net session >nul 2>&1
if errorlevel 1 (
  echo Requesting Administrator permission...
  powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b 0
)

set "APP=C:\ProgramData\ZYNTRASEC"
set "SERVICE=ZYNTRASECWatchdog"

echo.
echo ================================================
echo        ZYNTRASEC FINAL FULL UNINSTALL
echo ================================================
echo.
echo This removes the installed ZYNTRASEC program, startup
 echo entries, service, scheduled tasks, watchdog and logs.
echo It does NOT delete this ZIP/folder or backups stored
 echo outside C:\ProgramData\ZYNTRASEC.
echo.
choice /C YN /N /M "Continue with FULL uninstall? [Y/N]: "
if errorlevel 2 exit /b 0

:: Stop known processes first
for %%P in (ZYNTRASEC_WATCHDOG_SERVICE.exe ZYNTRASEC_WATCHDOG.exe ZYNTRASEC_EVENT_MONITOR.exe ZYNTRASEC_LOCKSCREEN.exe ZYNTRASEC_SECURITY_CONSOLE.exe ZYNTRASEC_INTEGRITY_CHECK.exe ZYNTRASEC_FACE_SETUP.exe) do (
  taskkill /F /IM "%%P" >nul 2>&1
)

:: Stop/delete known service
sc.exe stop "%SERVICE%" >nul 2>&1
sc.exe delete "%SERVICE%" >nul 2>&1

:: Remove any scheduled task whose name/path contains ZYNTRASEC
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='SilentlyContinue'; Get-ScheduledTask | Where-Object { $_.TaskName -like '*ZYNTRASEC*' -or $_.TaskPath -like '*ZYNTRASEC*' } | ForEach-Object { Unregister-ScheduledTask -TaskName $_.TaskName -TaskPath $_.TaskPath -Confirm:$false }"

:: Remove HKCU/HKLM Run entries used by ZYNTRASEC
for %%K in ("HKCU\Software\Microsoft\Windows\CurrentVersion\Run" "HKLM\Software\Microsoft\Windows\CurrentVersion\Run") do (
  reg.exe delete %%K /v "ZYNTRASEC Face Security" /f >nul 2>&1
  reg.exe delete %%K /v "ZYNTRASEC Event Monitor" /f >nul 2>&1
  reg.exe delete %%K /v "ZYNTRASEC Watchdog" /f >nul 2>&1
)

:: Remove ZYNTRASEC items from the current user's Startup folder
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$s=[Environment]::GetFolderPath('Startup'); Get-ChildItem -LiteralPath $s -Force -ErrorAction SilentlyContinue | Where-Object { $_.Name -like '*ZYNTRASEC*' } | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue"

:: Remove installed ZYNTRASEC directory (including config, logs and installed face model)
if exist "%APP%" (
  attrib -R -A -S -H "%APP%" /S /D >nul 2>&1
  rmdir /S /Q "%APP%" >nul 2>&1
)

:: One more process cleanup in case a process restarted during uninstall
for %%P in (ZYNTRASEC_WATCHDOG_SERVICE.exe ZYNTRASEC_WATCHDOG.exe ZYNTRASEC_EVENT_MONITOR.exe ZYNTRASEC_LOCKSCREEN.exe ZYNTRASEC_SECURITY_CONSOLE.exe ZYNTRASEC_INTEGRITY_CHECK.exe ZYNTRASEC_FACE_SETUP.exe) do (
  taskkill /F /IM "%%P" >nul 2>&1
)

echo.
echo ================================================
echo FULL UNINSTALL COMPLETE
 echo ================================================
echo.
echo Installed ZYNTRASEC components and startup entries were removed.
echo The V32 backup inside your downloaded package was NOT touched.
echo A reboot is recommended to release any remaining file locks.
echo.
pause
endlocal
