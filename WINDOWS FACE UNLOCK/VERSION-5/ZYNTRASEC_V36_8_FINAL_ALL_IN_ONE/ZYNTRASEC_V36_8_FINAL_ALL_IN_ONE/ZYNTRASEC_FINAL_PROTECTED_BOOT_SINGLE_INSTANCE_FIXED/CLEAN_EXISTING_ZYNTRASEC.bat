@echo off
setlocal EnableExtensions
title ZYNTRASEC FINAL - SAFE CLEAN / BACKUP

net session >nul 2>&1
if errorlevel 1 (
  echo ERROR: Run as Administrator.
  exit /b 1
)

set "APP=%ProgramData%\ZYNTRASEC"
set "BACKROOT=%ProgramData%\ZYNTRASEC_Backups"
for /f %%T in ('powershell.exe -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "STAMP=%%T"
set "BACK=%BACKROOT%\%STAMP%"

echo ============================================================
echo ZYNTRASEC - SAFE CLEAN / BACKUP
echo ============================================================

echo [1] Stopping service...
sc.exe stop ZYNTRASECWatchdog >nul 2>&1
timeout /t 3 /nobreak >nul

echo [2] Stopping ZYNTRASEC processes...
for %%P in (
 ZYNTRASEC_WATCHDOG_SERVICE.exe
 ZYNTRASEC_WATCHDOG_AGENT.exe
 ZYNTRASEC_EVENT_MONITOR.exe
 ZYNTRASEC_LOCKSCREEN.exe
 ZYNTRASEC_SECURITY_CONSOLE.exe
 ZYNTRASEC_INTEGRITY_CHECK.exe
 ZYNTRASEC_FACE_SETUP.exe
) do taskkill.exe /F /IM "%%P" >nul 2>&1

timeout /t 2 /nobreak >nul

echo [3] Removing old scheduled tasks...
for %%T in (
 "ZYNTRASEC Boot Service Recovery"
 "ZYNTRASEC Logon Service Recovery"
 "ZYNTRASEC User Event Monitor"
 "ZYNTRASEC Event Monitor Backup"
 "ZYNTRASEC Logon Service"
 "ZYNTRASEC Boot Service"
) do schtasks.exe /Delete /TN %%T /F >nul 2>&1

echo [4] Removing old service...
sc.exe delete ZYNTRASECWatchdog >nul 2>&1
timeout /t 2 /nobreak >nul

echo [5] Removing startup entries...
reg.exe delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "ZYNTRASEC Face Security" /f >nul 2>&1
reg.exe delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "ZYNTRASEC Event Monitor" /f >nul 2>&1
reg.exe delete "HKLM\Software\Microsoft\Windows\CurrentVersion\Run" /v "ZYNTRASEC Face Security" /f >nul 2>&1
reg.exe delete "HKLM\Software\Microsoft\Windows\CurrentVersion\Run" /v "ZYNTRASEC Event Monitor" /f >nul 2>&1

if not exist "%APP%" (
  echo No old ZYNTRASEC installation found.
  exit /b 0
)

echo [6] Creating external backup...
mkdir "%BACKROOT%" >nul 2>&1
mkdir "%BACK%" >nul 2>&1
robocopy "%APP%" "%BACK%\ZYNTRASEC" /E /R:2 /W:1 /XJ /NFL /NDL /NJH /NJS ^
 /XD "%APP%\Backup" "%APP%\Backups" "%APP%\CredentialProvider_Backups" "%APP%\OneClickBackups" >nul
set "RRC=%ERRORLEVEL%"
if %RRC% GEQ 8 (
  echo ERROR: Backup failed. Robocopy exit code %RRC%.
  echo Old installation was NOT deleted.
  exit /b 2
)
echo Backup complete: %BACK%

echo [7] Deleting old installed files...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
 "$p='C:\ProgramData\ZYNTRASEC'; if(Test-Path -LiteralPath $p){ Remove-Item -LiteralPath $p -Recurse -Force -ErrorAction Stop }"
if errorlevel 1 (
  echo ERROR: Windows still has a file locked inside C:\ProgramData\ZYNTRASEC.
  echo Backup is preserved and old installation was NOT removed.
  exit /b 3
)

if exist "%APP%" (
  echo ERROR: Old ZYNTRASEC folder still exists.
  exit /b 4
)

echo CLEAN COMPLETE.
echo Backup: %BACK%
exit /b 0
