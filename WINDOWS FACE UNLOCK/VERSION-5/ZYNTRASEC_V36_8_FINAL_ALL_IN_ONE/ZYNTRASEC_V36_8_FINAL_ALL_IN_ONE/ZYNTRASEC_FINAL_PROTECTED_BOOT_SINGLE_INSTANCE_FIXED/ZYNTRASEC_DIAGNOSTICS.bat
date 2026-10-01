@echo off
cd /d "%~dp0"
set "ROOT=%ProgramData%\ZYNTRASEC\System"
if exist "%ROOT%\ZYNTRASEC_DIAGNOSTICS.exe" ("%ROOT%\ZYNTRASEC_DIAGNOSTICS.exe") else (echo Build/install ZYNTRASEC first.)
pause
