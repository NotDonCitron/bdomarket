@echo off
REM BDO Pearl Monitor - Browser Mode
REM Opens all 8 Pearl categories in browser tabs with live DOM monitoring

echo ========================================
echo BDO Pearl Monitor - BROWSER MODE
echo ========================================
echo.
echo Features:
echo   - 8 Browser-Tabs mit Pearl-Kategorien
echo   - Live DOM-Aenderungs-Erkennung
echo   - Sofortige Alerts bei neuen Items
echo   - Backup 5s Polling pro Tab
echo.
echo Press CTRL+C to stop
echo ========================================
echo.

.venv\Scripts\python.exe pearl_monitor_browser.py

pause

