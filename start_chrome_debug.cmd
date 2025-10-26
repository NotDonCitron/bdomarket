@echo off
echo Starting Chrome with remote debugging enabled...
echo.
echo IMPORTANT: Close all existing Chrome windows before running this!
echo.
pause

REM Start Chrome with remote debugging
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%TEMP%\chrome-profile-debug"




