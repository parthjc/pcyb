@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title PCYBI FINAL // PROTECTED BOOT INSTALL
net session >nul 2>&1 || (powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs" & exit /b 0)
set "ROOT=%ProgramData%\PCYBI\System"
set "APP=%ProgramData%\PCYBI"
set "SERVICE=PCYBIWatchdog"

echo ============================================================
echo PCYBI FINAL - PROTECTED BOOT INSTALL
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

:: Stop old components and remove old PCYBI scheduled tasks before copying.
sc.exe stop "%SERVICE%" >nul 2>&1
for %%P in (PCYBI_WATCHDOG_SERVICE.exe PCYBI_WATCHDOG_AGENT.exe PCYBI_EVENT_MONITOR.exe PCYBI_LOCKSCREEN.exe PCYBI_SECURITY_CONSOLE.exe PCYBI_INTEGRITY_CHECK.exe PCYBI_FACE_SETUP.exe) do taskkill /F /IM "%%P" >nul 2>&1
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='SilentlyContinue'; Get-ScheduledTask | Where-Object { $_.TaskName -like '*PCYBI*' -or $_.TaskPath -like '*PCYBI*' } | ForEach-Object { Unregister-ScheduledTask -TaskName $_.TaskName -TaskPath $_.TaskPath -Confirm:$false }" >nul 2>&1
sc.exe delete "%SERVICE%" >nul 2>&1
for /L %%N in (1,1,20) do (
  sc.exe query "%SERVICE%" >nul 2>&1
  if errorlevel 1 goto SERVICE_REMOVED
  timeout /t 1 /nobreak >nul
)
:SERVICE_REMOVED

:: Remove legacy Run entries. Startup Apps is NOT used by PCYBI.
for %%R in ("HKLM\Software\Microsoft\Windows\CurrentVersion\Run" "HKCU\Software\Microsoft\Windows\CurrentVersion\Run") do (
  reg.exe delete %%R /v "PCYBI Face Security" /f >nul 2>&1
  reg.exe delete %%R /v "PCYBI Event Monitor" /f >nul 2>&1
  reg.exe delete %%R /v "PCYBI Watchdog" /f >nul 2>&1
)

:: Copy built components.
for %%F in (PCYBI_FACE_SETUP.exe PCYBI_WATCHDOG_SERVICE.exe PCYBI_EVENT_MONITOR.exe PCYBI_LOCKSCREEN.exe PCYBI_SECURITY_CONSOLE.exe PCYBI_INTEGRITY_CHECK.exe PCYBI_DIAGNOSTICS.exe PCYBI_CONTROL_CENTER.exe PCYBI_BACKUP.exe PCYBI_HEALTH_CHECK.exe PCYBI_ADVANCED_CONTROL_CENTER.exe PCYBI_ALL_IN_ONE.exe PCYBI_FINAL_TEST.exe) do (
  if not exist "dist\%%F" (echo MISSING dist\%%F & exit /b 2)
  copy /y "dist\%%F" "%ROOT%\%%F" >nul || exit /b 2
)

:: Register the service in DEMAND mode first. The guided setup starts it only
:: after owner face/password registration has completed.
sc.exe create "%SERVICE%" binPath= "\"%ROOT%\PCYBI_WATCHDOG_SERVICE.exe\"" start= demand type= own obj= LocalSystem DisplayName= "PCYBI Security Watchdog" || exit /b 2
sc.exe config "%SERVICE%" binPath= "\"%ROOT%\PCYBI_WATCHDOG_SERVICE.exe\"" >nul 2>&1 || exit /b 2
sc.exe description "%SERVICE%" "PCYBI protected boot watchdog service" >nul
sc.exe failure "%SERVICE%" reset=86400 actions=restart/5000/restart/10000/restart/30000 >nul

:: Launch the guided setup. It enables AUTO_START and creates the recovery
:: tasks only after registration has succeeded.
call "%~dp0FIRST_RUN_SETUP.bat"
if errorlevel 1 (
  echo.
  echo ============================================================
  echo PCYBI FINAL INSTALL/SETUP FAILED
  echo Existing backups were preserved.
  echo ============================================================
  exit /b 3
)

exit /b 0
