@echo off
setlocal EnableExtensions
title PCYBI FINAL - SAFE CLEAN / BACKUP

net session >nul 2>&1
if errorlevel 1 (
  echo ERROR: Run as Administrator.
  exit /b 1
)

set "APP=%ProgramData%\PCYBI"
set "BACKROOT=%ProgramData%\PCYBI_Backups"
for /f %%T in ('powershell.exe -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "STAMP=%%T"
set "BACK=%BACKROOT%\%STAMP%"

echo ============================================================
echo PCYBI - SAFE CLEAN / BACKUP
echo ============================================================

echo [1] Stopping service...
sc.exe stop PCYBIWatchdog >nul 2>&1
timeout /t 3 /nobreak >nul

echo [2] Stopping PCYBI processes...
for %%P in (
 PCYBI_WATCHDOG_SERVICE.exe
 PCYBI_WATCHDOG_AGENT.exe
 PCYBI_EVENT_MONITOR.exe
 PCYBI_LOCKSCREEN.exe
 PCYBI_SECURITY_CONSOLE.exe
 PCYBI_INTEGRITY_CHECK.exe
 PCYBI_FACE_SETUP.exe
) do taskkill.exe /F /IM "%%P" >nul 2>&1

timeout /t 2 /nobreak >nul

echo [3] Removing old scheduled tasks...
for %%T in (
 "PCYBI Boot Service Recovery"
 "PCYBI Logon Service Recovery"
 "PCYBI User Event Monitor"
 "PCYBI Event Monitor Backup"
 "PCYBI Logon Service"
 "PCYBI Boot Service"
) do schtasks.exe /Delete /TN %%T /F >nul 2>&1

echo [4] Removing old service...
sc.exe delete PCYBIWatchdog >nul 2>&1
timeout /t 2 /nobreak >nul

echo [5] Removing startup entries...
reg.exe delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "PCYBI Face Security" /f >nul 2>&1
reg.exe delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "PCYBI Event Monitor" /f >nul 2>&1
reg.exe delete "HKLM\Software\Microsoft\Windows\CurrentVersion\Run" /v "PCYBI Face Security" /f >nul 2>&1
reg.exe delete "HKLM\Software\Microsoft\Windows\CurrentVersion\Run" /v "PCYBI Event Monitor" /f >nul 2>&1

if not exist "%APP%" (
  echo No old PCYBI installation found.
  exit /b 0
)

echo [6] Creating external backup...
mkdir "%BACKROOT%" >nul 2>&1
mkdir "%BACK%" >nul 2>&1
robocopy "%APP%" "%BACK%\PCYBI" /E /R:2 /W:1 /XJ /NFL /NDL /NJH /NJS ^
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
 "$p='C:\ProgramData\PCYBI'; if(Test-Path -LiteralPath $p){ Remove-Item -LiteralPath $p -Recurse -Force -ErrorAction Stop }"
if errorlevel 1 (
  echo ERROR: Windows still has a file locked inside C:\ProgramData\PCYBI.
  echo Backup is preserved and old installation was NOT removed.
  exit /b 3
)

if exist "%APP%" (
  echo ERROR: Old PCYBI folder still exists.
  exit /b 4
)

echo CLEAN COMPLETE.
echo Backup: %BACK%
exit /b 0
