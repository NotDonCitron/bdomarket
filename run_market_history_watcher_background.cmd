@echo off
REM Run market history watcher in background (no console window)

echo Starting Market History Watcher in background...
echo Check data/market_history/recorder.log for activity.
echo.

start /B pythonw watch_market_history.py

echo Watcher started in background.
echo.
pause

