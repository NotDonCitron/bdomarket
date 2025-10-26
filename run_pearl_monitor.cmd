@echo off
REM Production Pearl Monitor - Runs indefinitely
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
.venv\Scripts\python.exe pearl_monitor_bdomarket.py --interval 2.0
pause

