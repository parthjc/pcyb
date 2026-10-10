@echo off
title ZYNTRASEC Universal HTML Engine - Auto Manual
cd /d "%~dp0"
py -3 "%~dp0ZYNTRASEC_UNIVERSAL_HTML_ENGINE_AUTO_MANUAL.py"
if errorlevel 1 python "%~dp0ZYNTRASEC_UNIVERSAL_HTML_ENGINE_AUTO_MANUAL.py"
