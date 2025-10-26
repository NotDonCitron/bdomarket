@echo off
REM BDO Pearl Monitor - Browser Mode mit MANUAL LOGIN
REM Oeffnet Browser und wartet bis du dich ueber Steam eingeloggt hast

echo ========================================
echo BDO Pearl Monitor - MANUAL LOGIN MODE
echo ========================================
echo.
echo Ablauf:
echo   1. Browser oeffnet sich
echo   2. Du loggst dich ueber Steam ein
echo   3. Du drueckst ENTER im Terminal
echo   4. Monitor startet mit 8 Tabs
echo.
echo ========================================
echo.

.venv\Scripts\python.exe pearl_monitor_browser.py --manual-login

pause

