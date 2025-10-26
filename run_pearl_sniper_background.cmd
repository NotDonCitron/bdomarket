@echo off
REM Pearl Item Sniper - Background Mode
REM Runs the pearl sniper in background (no console window)

echo ========================================
echo    BDO Pearl Item Sniper - Background
echo ========================================
echo.
echo Starting pearl sniper in background mode...
echo Check Windows notifications for alerts.
echo.

start "" pythonw pearl_sniper.py

echo Pearl Sniper is now running in the background!
echo To stop it, use Task Manager and end the pythonw.exe process.
echo.
pause

