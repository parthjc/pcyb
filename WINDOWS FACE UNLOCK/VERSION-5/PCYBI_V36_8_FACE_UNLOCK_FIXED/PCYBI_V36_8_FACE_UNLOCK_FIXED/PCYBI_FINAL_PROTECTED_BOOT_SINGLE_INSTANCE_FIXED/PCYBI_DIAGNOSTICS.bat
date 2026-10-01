@echo off
cd /d "%~dp0"
set "ROOT=%ProgramData%\PCYBI\System"
if exist "%ROOT%\PCYBI_DIAGNOSTICS.exe" ("%ROOT%\PCYBI_DIAGNOSTICS.exe") else (echo Build/install PCYBI first.)
pause
