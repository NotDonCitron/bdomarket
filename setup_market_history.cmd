@echo off
REM Setup and test market history tracking

echo ========================================
echo Market History Tracker - Setup
echo ========================================
echo.

echo Step 1: Recording first snapshot...
echo (This takes 10-20 seconds)
echo.
python record_market_snapshot.py

if errorlevel 1 (
    echo.
    echo ERROR: Failed to record snapshot!
    echo Check your internet connection and bdomarket installation.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Step 2: Checking data...
echo ========================================
echo.
python record_market_snapshot.py --summary

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Your historical database is now initialized.
echo.
echo Next steps:
echo   1. Run this daily: record_market_snapshot.cmd
echo   2. Or run 24/7: run_market_history_watcher.cmd
echo   3. See examples: python example_market_history.py
echo.
echo See MARKET_HISTORY_GUIDE.md for full documentation
echo.
pause

