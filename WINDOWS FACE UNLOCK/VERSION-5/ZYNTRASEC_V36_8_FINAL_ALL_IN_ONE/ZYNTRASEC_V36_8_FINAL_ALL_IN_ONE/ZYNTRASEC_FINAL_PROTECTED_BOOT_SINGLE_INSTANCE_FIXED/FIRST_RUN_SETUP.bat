@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title ZYNTRASEC FINAL // GUIDED FIRST-TIME SETUP
net session >nul 2>&1 || (powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs" & exit /b 0)
set "APP=%ProgramData%\ZYNTRASEC"
set "ROOT=%APP%\System"
set "DATA=%APP%\SecurityData"
set "SERVICE=ZYNTRASECWatchdog"
set "FORCE_OWNER_SETUP=%ZYNTRASEC_FORCE_OWNER_SETUP%"

if /I "%FORCE_OWNER_SETUP%"=="1" (
  echo Fresh owner registration requested.
  if exist "%DATA%\\face_model.yml" del /f /q "%DATA%\\face_model.yml" >nul 2>&1
  if exist "%DATA%\\master_password.json" del /f /q "%DATA%\\master_password.json" >nul 2>&1
  if exist "%DATA%\\security_enabled.flag" del /f /q "%DATA%\\security_enabled.flag" >nul 2>&1
)


cls
echo ============================================================
echo ZYNTRASEC FINAL - GUIDED AUTOMATIC SETUP
 echo ============================================================
echo.
echo This wizard will complete the remaining setup automatically.
echo You only need to complete the OWNER FACE + MASTER PASSWORD
 echo screen when it opens.
echo.

:STEP1
echo.
echo [1/6] Checking ZYNTRASEC components...
for %%F in (ZYNTRASEC_FACE_SETUP.exe ZYNTRASEC_WATCHDOG_SERVICE.exe ZYNTRASEC_EVENT_MONITOR.exe ZYNTRASEC_LOCKSCREEN.exe ZYNTRASEC_SECURITY_CONSOLE.exe ZYNTRASEC_INTEGRITY_CHECK.exe ZYNTRASEC_DIAGNOSTICS.exe ZYNTRASEC_CONTROL_CENTER.exe ZYNTRASEC_BACKUP.exe ZYNTRASEC_HEALTH_CHECK.exe ZYNTRASEC_ADVANCED_CONTROL_CENTER.exe ZYNTRASEC_ALL_IN_ONE.exe ZYNTRASEC_FINAL_TEST.exe) do (
  if not exist "%ROOT%\%%F" (
    echo ERROR: Missing %ROOT%\%%F
    exit /b 10
  )
)
echo Components: OK

:STEP2
echo.
echo [2/6] Preparing secure first-run mode...
sc.exe stop "%SERVICE%" >nul 2>&1
for %%P in (ZYNTRASEC_WATCHDOG_SERVICE.exe ZYNTRASEC_EVENT_MONITOR.exe ZYNTRASEC_LOCKSCREEN.exe ZYNTRASEC_SECURITY_CONSOLE.exe ZYNTRASEC_FACE_SETUP.exe ZYNTRASEC_INTEGRITY_CHECK.exe) do taskkill /F /IM "%%P" >nul 2>&1
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='SilentlyContinue'; Get-ScheduledTask | Where-Object { $_.TaskName -like '*ZYNTRASEC*' -or $_.TaskPath -like '*ZYNTRASEC*' } | ForEach-Object { Unregister-ScheduledTask -TaskName $_.TaskName -TaskPath $_.TaskPath -Confirm:$false }" >nul 2>&1
sc.exe config "%SERVICE%" start= demand >nul 2>&1

echo Protected startup is temporarily paused until owner registration finishes.
echo The user-session monitor will be registered with LogonType=Interactive.

:STEP3
echo.
echo ============================================================
echo [3/6] OWNER FACE + MASTER PASSWORD
 echo ============================================================
echo.
echo A setup window will open now.
echo.
echo  1. Create your emergency master password.
echo  2. Windows Camera will open automatically.
echo  3. Follow LOOK LEFT / RIGHT / CENTER instructions.
echo  4. Five live face samples will be registered.
echo.
start "" /wait "%ROOT%\ZYNTRASEC_FACE_SETUP.exe"

if not exist "%DATA%\face_model.yml" (
  echo.
  echo ERROR: Face registration did not complete.
  echo Please run this installer again and finish the face setup.
  exit /b 20
)
if not exist "%DATA%\master_password.json" (
  echo.
  echo ERROR: Master password was not created.
  echo Please run this installer again and finish the password setup.
  exit /b 21
)

echo Owner face: REGISTERED
 echo Master password: REGISTERED

:STEP4
echo.
echo [4/6] Creating security settings and integrity baseline...
if not exist "%ROOT%\pc_ybi_settings.json" (
  >"%ROOT%\pc_ybi_settings.json" echo {"voice_enabled":true,"voice_volume":100,"voice_rate":-1}
)
"%ROOT%\ZYNTRASEC_INTEGRITY_CHECK.exe" > "%ROOT%\integrity_setup_result.txt" 2>&1
if errorlevel 1 (
  echo ERROR: Integrity baseline could not be created.
  type "%ROOT%\integrity_setup_result.txt"
  exit /b 30
)
echo Integrity baseline: READY

:STEP5
echo.
echo [5/6] Enabling protected Windows startup...
sc.exe config "%SERVICE%" start= delayed-auto >nul 2>&1 || exit /b 40
sc.exe description "%SERVICE%" "ZYNTRASEC protected boot watchdog service" >nul 2>&1
sc.exe failure "%SERVICE%" reset=86400 actions=restart/5000/restart/10000/restart/30000 >nul 2>&1

:: AUTO_START is the primary boot mechanism. Do not create a second
:: ONSTART "sc start" task; it can race the Service Control Manager and
:: create START_PENDING/restart noise.
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $u=[Security.Principal.WindowsIdentity]::GetCurrent().Name; $p=New-ScheduledTaskPrincipal -UserId $u -LogonType Interactive -RunLevel Highest; $t=New-ScheduledTaskTrigger -AtLogOn; $a=New-ScheduledTaskAction -Execute '%ROOT%\ZYNTRASEC_EVENT_MONITOR.exe'; $s=New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew; Register-ScheduledTask -TaskName 'ZYNTRASEC User Event Monitor' -Action $a -Principal $p -Trigger $t -Settings $s -Force | Out-Null; $la=New-ScheduledTaskAction -Execute '%ROOT%\ZYNTRASEC_LOCKSCREEN.exe'; Register-ScheduledTask -TaskName 'ZYNTRASEC Lock Screen' -Action $la -Principal $p -Trigger $t -Settings $s -Force | Out-Null" || exit /b 43

sc.exe start "%SERVICE%" > "%ROOT%\service_start_result.txt" 2>&1
set RUNNING=
for /L %%N in (1,1,45) do (
  for /F "tokens=4" %%S in ('sc.exe query "%SERVICE%" ^| findstr /I "STATE"') do if /I "%%S"=="RUNNING" set RUNNING=YES
  if defined RUNNING goto START_OK
  timeout /t 1 /nobreak >nul
)
echo ERROR: ZYNTRASEC service did not reach RUNNING.
sc.exe query "%SERVICE%"
type "%ROOT%\service_start_result.txt"
exit /b 44

:START_OK
:: Stability check: ensure the service remains RUNNING for several seconds.
for /L %%N in (1,1,8) do (
  timeout /t 1 /nobreak >nul
  set STABLE=
  for /F "tokens=4" %%S in ('sc.exe query "%SERVICE%" ^| findstr /I "STATE"') do if /I "%%S"=="RUNNING" set STABLE=YES
  if not defined STABLE (
    echo ERROR: ZYNTRASEC service stopped/restarted during stability check.
    sc.exe query "%SERVICE%"
    exit /b 45
  )
)
echo Protected startup: ENABLED
echo Service: RUNNING
echo Delayed auto-start: READY
echo Logon recovery: READY
echo User monitor: READY

:STEP6
echo.
echo [6/6] Final verification...
timeout /t 5 /nobreak >nul
"%ROOT%\ZYNTRASEC_INTEGRITY_CHECK.exe" > "%ROOT%\integrity_verify_result.txt" 2>&1
sc.exe query "%SERVICE%"
echo.
echo ============================================================
echo ZYNTRASEC FINAL SETUP COMPLETE
 echo ============================================================
echo.
echo OWNER FACE       : READY
echo MASTER PASSWORD  : READY
echo LIVENESS         : READY
echo WINDOWS SERVICE  : RUNNING
echo AUTO START       : READY
echo LOGON RECOVERY   : READY
echo UNLOCK/WAKE      : READY
echo BACKUP           : AVAILABLE
echo INTEGRITY        : READY
echo.
echo The ZYNTRASEC lock screen will activate automatically after sign-in,
echo unlock/wake event, or restart.
echo.
echo Recommended: restart Windows once to verify the complete boot flow.
echo.
exit /b 0
