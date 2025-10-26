@echo off
REM Fill the values between quotes. Do NOT add spaces.
set "COOKIE_TOKEN=tu_YxtfBRzT5aAiho2tFT3xmhLdFE1J7Y0GRHVHpxH_0LE5bjz3iL103jvk6MbiKQ54Amh7Nxc6plfqbXRDAzJWcAXJ5eCgDz9g_fZQzq0Y1"
set "FORM_TOKEN=yoghfavLqJ7aqMLOj1ixUBZS5q1eO1hc01o8gO_5fzmGEncRCa3gpGN2Me1rBvxwl3wChpG6213-JOzNyD8zboLgw8M9SPoN3MhoxTPdSSw1"
set "NAEU_SESSION="
set "TRADE_AUTH=nxqsk00gv1bm3njrqj2t0wum"
set "WEBHOOK=PUT_YOUR_DISCORD_WEBHOOK_URL_HERE"

REM If you do NOT have NAEU_SESSION but you have ASP.NET_SessionId, set it here and add --session below
set "ASPNET_SESSION="

echo Starting fast pearl watcher...
node "C:\Users\kekww\Desktop\bdo marketplace tool\watch_pearl_fast.mjs" --region eu --poll 300 ^
  --cookie-token "%COOKIE_TOKEN%" --form-token "%FORM_TOKEN%" ^
  --naeu-session "%NAEU_SESSION%" --trade-auth "%TRADE_AUTH%" ^
  --webhook "%WEBHOOK%" %EXTRA%

REM To use ASP.NET_SessionId instead of naeu.Session, replace the command above with this one:
REM node "C:\Users\kekww\Desktop\bdo marketplace tool\watch_pearl_fast.mjs" --region eu --poll 300 ^
REM   --cookie-token "%COOKIE_TOKEN%" --form-token "%FORM_TOKEN%" ^
REM   --session "%ASPNET_SESSION%" --trade-auth "%TRADE_AUTH%" ^
REM   --webhook "%WEBHOOK%"

pause
