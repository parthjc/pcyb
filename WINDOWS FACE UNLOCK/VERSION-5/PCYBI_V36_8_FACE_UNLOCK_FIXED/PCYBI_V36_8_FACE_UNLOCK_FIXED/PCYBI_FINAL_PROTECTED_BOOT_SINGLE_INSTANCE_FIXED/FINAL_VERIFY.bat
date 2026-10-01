@echo off
title PCYBI V32 - FINAL VERIFY
setlocal
net session >nul 2>&1
if errorlevel 1 (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process '%~f0' -Verb RunAs"
  exit /b
)

echo ============================================================
echo PCYBI V32 FINAL STABLE - VERIFY
echo ============================================================
echo.

echo [1] Service
sc.exe query PCYBIWatchdog
echo.

echo [2] Installed folder
if exist "C:\ProgramData\PCYBI" (
  echo C:\ProgramData\PCYBI : PRESENT
) else (
  echo C:\ProgramData\PCYBI : NOT FOUND
)

echo.
echo [3] Key components
for %%F in (
 "PCYBI_LOCKSCREEN.exe"
 "PCYBI_EVENT_MONITOR.exe"
 "PCYBI_WATCHDOG_SERVICE.exe"
) do (
  if exist "C:\ProgramData\PCYBI\%%~F" (
    echo %%~F : PRESENT
  ) else (
    echo %%~F : not found
  )
)

echo.
echo [4] Recent backups
if exist "C:\ProgramData\PCYBI_Backups" (
  dir /b /ad /o-d "C:\ProgramData\PCYBI_Backups" 2>nul
) else (
  echo No external backup directory found.
)

echo.
echo Verification is read-only. Nothing was changed.
pause
