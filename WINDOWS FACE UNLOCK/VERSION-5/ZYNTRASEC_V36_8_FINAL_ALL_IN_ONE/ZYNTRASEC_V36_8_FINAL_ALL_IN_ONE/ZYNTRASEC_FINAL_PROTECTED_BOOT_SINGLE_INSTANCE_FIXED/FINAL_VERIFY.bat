@echo off
title ZYNTRASEC V32 - FINAL VERIFY
setlocal
net session >nul 2>&1
if errorlevel 1 (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process '%~f0' -Verb RunAs"
  exit /b
)

echo ============================================================
echo ZYNTRASEC V32 FINAL STABLE - VERIFY
echo ============================================================
echo.

echo [1] Service
sc.exe query ZYNTRASECWatchdog
echo.

echo [2] Installed folder
if exist "C:\ProgramData\ZYNTRASEC" (
  echo C:\ProgramData\ZYNTRASEC : PRESENT
) else (
  echo C:\ProgramData\ZYNTRASEC : NOT FOUND
)

echo.
echo [3] Key components
for %%F in (
 "ZYNTRASEC_LOCKSCREEN.exe"
 "ZYNTRASEC_EVENT_MONITOR.exe"
 "ZYNTRASEC_WATCHDOG_SERVICE.exe"
) do (
  if exist "C:\ProgramData\ZYNTRASEC\%%~F" (
    echo %%~F : PRESENT
  ) else (
    echo %%~F : not found
  )
)

echo.
echo [4] Recent backups
if exist "C:\ProgramData\ZYNTRASEC_Backups" (
  dir /b /ad /o-d "C:\ProgramData\ZYNTRASEC_Backups" 2>nul
) else (
  echo No external backup directory found.
)

echo.
echo Verification is read-only. Nothing was changed.
pause
