@echo off
REM Long-running Pearl Monitor Test
REM Runs with 5 second interval for extended period
REM Output logged to pearl_monitor_longrun.log

echo ========================================
echo BDO Pearl Monitor - Long Run Test
echo ========================================
echo Interval: 5.0s
echo Log: pearl_monitor_longrun.log
echo Press CTRL+C to stop
echo ========================================
echo.

.venv\Scripts\python.exe pearl_monitor_parallel.py --interval 5.0 --config config/trader_auth.json > pearl_monitor_longrun.log 2>&1


