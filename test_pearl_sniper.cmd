@echo off
REM Pearl Item Sniper - Test Mode
REM Tests the pearl sniper with mock data

echo ========================================
echo    BDO Pearl Item Sniper - TEST MODE
echo ========================================
echo.
echo Running pearl sniper with mock data...
echo This will test all components without hitting the live API.
echo.

python pearl_sniper.py --test

echo.
echo Test completed!
echo.
pause

