@echo off
REM Run market history watcher continuously
REM This will record snapshots at midnight every day

echo Starting Market History Watcher...
echo This will run continuously and record data at midnight.
echo Press Ctrl+C to stop.
echo.

python watch_market_history.py

pause

