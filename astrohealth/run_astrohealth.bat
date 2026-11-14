@echo off
title AstroHealth Launcher
echo ==================================================
echo    Starting ASTROHEALTH Mission Control System
echo ==================================================

powershell -ExecutionPolicy Bypass -File "%~dp0run_astrohealth.ps1"
pause

