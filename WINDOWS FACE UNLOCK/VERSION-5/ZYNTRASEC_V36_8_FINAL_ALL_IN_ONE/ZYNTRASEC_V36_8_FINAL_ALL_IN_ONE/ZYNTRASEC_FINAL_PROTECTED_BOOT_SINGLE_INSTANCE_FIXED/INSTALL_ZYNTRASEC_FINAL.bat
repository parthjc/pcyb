@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title ZYNTRASEC FINAL // PROTECTED BOOT INSTALL
net session >nul 2>&1 || (powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs" & exit /b 0)
set "ROOT=%ProgramData%\ZYNTRASEC\System"
set "APP=%ProgramData%\ZYNTRASEC"
set "SERVICE=ZYNTRASECWatchdog"

echo ============================================================
echo ZYNTRASEC FINAL - PROTECTED BOOT INSTALL
echo ============================================================
echo.

if not exist "%ROOT%" mkdir "%ROOT%"

:: Preserve current installation before replacement.
if exist "%APP%" (
  for /f %%T in ('powershell.exe -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "STAMP=%%T"
  if not defined STAMP set "STAMP=BEFORE_INSTALL"
  mkdir "%APP%\Backup\BEFORE_INSTALL_!STAMP!" >nul 2>&1
  robocopy "%APP%" "%APP%\Backup\BEFORE_INSTALL_!STAMP!" /E /XD "%APP%\Backup" >nul
  echo Backup created: %APP%\Backup\BEFORE_INSTALL_!STAMP!
)

:: Stop old components and remove old ZYNTRASEC scheduled tasks before copying.
sc.exe stop "%SERVICE%" >nul 2>&1
for %%P in (ZYNTRASEC_WATCHDOG_SERVICE.exe ZYNTRASEC_WATCHDOG_AGENT.exe ZYNTRASEC_EVENT_MONITOR.exe ZYNTRASEC_LOCKSCREEN.exe ZYNTRASEC_SECURITY_CONSOLE.exe ZYNTRASEC_INTEGRITY_CHECK.exe ZYNTRASEC_FACE_SETUP.exe) do taskkill /F /IM "%%P" >nul 2>&1
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='SilentlyContinue'; Get-ScheduledTask | Where-Object { $_.TaskName -like '*ZYNTRASEC*' -or $_.TaskPath -like '*ZYNTRASEC*' } | ForEach-Object { Unregister-ScheduledTask -TaskName $_.TaskName -TaskPath $_.TaskPath -Confirm:$false }" >nul 2>&1
sc.exe delete "%SERVICE%" >nul 2>&1
for /L %%N in (1,1,20) do (
  sc.exe query "%SERVICE%" >nul 2>&1
  if errorlevel 1 goto SERVICE_REMOVED
  timeout /t 1 /nobreak >nul
)
:SERVICE_REMOVED

:: Remove legacy Run entries. Startup Apps is NOT used by ZYNTRASEC.
for %%R in ("HKLM\Software\Microsoft\Windows\CurrentVersion\Run" "HKCU\Software\Microsoft\Windows\CurrentVersion\Run") do (
  reg.exe delete %%R /v "ZYNTRASEC Face Security" /f >nul 2>&1
  reg.exe delete %%R /v "ZYNTRASEC Event Monitor" /f >nul 2>&1
  reg.exe delete %%R /v "ZYNTRASEC Watchdog" /f >nul 2>&1
)

:: Copy built components.
for %%F in (ZYNTRASEC_FACE_SETUP.exe ZYNTRASEC_WATCHDOG_SERVICE.exe ZYNTRASEC_EVENT_MONITOR.exe ZYNTRASEC_LOCKSCREEN.exe ZYNTRASEC_SECURITY_CONSOLE.exe ZYNTRASEC_INTEGRITY_CHECK.exe ZYNTRASEC_DIAGNOSTICS.exe ZYNTRASEC_CONTROL_CENTER.exe ZYNTRASEC_BACKUP.exe ZYNTRASEC_HEALTH_CHECK.exe ZYNTRASEC_ADVANCED_CONTROL_CENTER.exe ZYNTRASEC_ALL_IN_ONE.exe ZYNTRASEC_FINAL_TEST.exe) do (
  if not exist "dist\%%F" (echo MISSING dist\%%F & exit /b 2)
  copy /y "dist\%%F" "%ROOT%\%%F" >nul || exit /b 2
)

:: Register the service in DEMAND mode first. The guided setup starts it only
:: after owner face/password registration has completed.
sc.exe create "%SERVICE%" binPath= "\"%ROOT%\ZYNTRASEC_WATCHDOG_SERVICE.exe\"" start= demand type= own obj= LocalSystem DisplayName= "ZYNTRASEC Security Watchdog" || exit /b 2
sc.exe config "%SERVICE%" binPath= "\"%ROOT%\ZYNTRASEC_WATCHDOG_SERVICE.exe\"" >nul 2>&1 || exit /b 2
sc.exe description "%SERVICE%" "ZYNTRASEC protected boot watchdog service" >nul
sc.exe failure "%SERVICE%" reset=86400 actions=restart/5000/restart/10000/restart/30000 >nul

:: Launch the guided setup. It enables AUTO_START and creates the recovery
:: tasks only after registration has succeeded.
call "%~dp0FIRST_RUN_SETUP.bat"
if errorlevel 1 (
  echo.
  echo ============================================================
  echo ZYNTRASEC FINAL INSTALL/SETUP FAILED
  echo Existing backups were preserved.
  echo ============================================================
  exit /b 3
)

exit /b 0
