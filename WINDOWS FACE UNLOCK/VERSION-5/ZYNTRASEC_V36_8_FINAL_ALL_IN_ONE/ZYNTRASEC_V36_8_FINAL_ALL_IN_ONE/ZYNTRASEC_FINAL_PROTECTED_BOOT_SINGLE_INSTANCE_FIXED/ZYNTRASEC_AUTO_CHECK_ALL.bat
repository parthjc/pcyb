@echo off
setlocal
set ROOT=%ProgramData%\ZYNTRASEC\System
set SERVICE=ZYNTRASECWatchdog
set OK=1
echo ============================================================
echo ZYNTRASEC // AUTO CHECK ALL
echo ============================================================
sc.exe query %SERVICE% | findstr /I "RUNNING" >nul || (echo [FAIL] Watchdog service & set OK=0)
schtasks.exe /Query /TN "ZYNTRASEC User Event Monitor" >nul 2>&1 || (echo [FAIL] User monitor task & set OK=0)
schtasks.exe /Query /TN "ZYNTRASEC Lock Screen" >nul 2>&1 || (echo [FAIL] Lock screen logon task & set OK=0)
if exist "%ROOT%\ZYNTRASEC_EVENT_MONITOR.exe" (echo [OK] Event monitor) else (echo [FAIL] Event monitor & set OK=0)
if exist "%ROOT%\ZYNTRASEC_LOCKSCREEN.exe" (echo [OK] Lock screen) else (echo [FAIL] Lock screen & set OK=0)
if exist "%ROOT%\ZYNTRASEC_WATCHDOG_SERVICE.exe" (echo [OK] Watchdog) else (echo [FAIL] Watchdog & set OK=0)
if exist "%ROOT%\watchdog.log" echo [OK] Watchdog log
if exist "%ROOT%\event_monitor.log" echo [OK] Event monitor log
if %OK%==1 (echo. & echo RESULT: READY - AUTO BOOT/LOGON/SLEEP-WAKE PATHS INSTALLED & exit /b 0)
echo. & echo RESULT: NEEDS REPAIR & exit /b 1
