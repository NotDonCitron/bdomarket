@echo off
REM Test single item monitor with Black Stone
chcp 65001 >nul
cd /d "%~dp0"
echo Testing single item monitor for 60 seconds...
timeout /t 60 /nobreak >nul & .venv\Scripts\python.exe pearl_monitor_watch_item.py 16001 --interval 1.0
pause

