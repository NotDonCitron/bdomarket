param(
  [string]$Region = 'eu',
  [int]$Poll = 300
)

Write-Host 'Ultra-fast Pearl queue watcher launcher' -ForegroundColor Cyan
Write-Host 'Paste tokens exactly as shown in DevTools (values stay local).' -ForegroundColor Yellow

$cookieToken = Read-Host '__RequestVerificationToken (cookie)'
$formToken   = Read-Host '__RequestVerificationToken (form data)'
$naeuSession = Read-Host 'naeu.Session (cookie) - optional'
$aspSession  = Read-Host 'ASP.NET_SessionId (cookie) - optional'
$tradeAuth   = Read-Host 'TradeAuth_Session_EU (cookie) - optional'
$webhook     = Read-Host 'Discord webhook URL - optional'

if (-not $cookieToken -or -not $formToken) {
  Write-Error 'cookieToken and formToken are required.'
  exit 1
}

$argsList = @(
  'C:\Users\kekww\Desktop\bdo marketplace tool\watch_pearl_fast.mjs',
  '--region', $Region,
  '--poll', $Poll,
  '--cookie-token', $cookieToken,
  '--form-token', $formToken
)

if ($naeuSession) { $argsList += @('--naeu-session', $naeuSession) }
elseif ($aspSession) { $argsList += @('--session', $aspSession) }
if ($tradeAuth)  { $argsList += @('--trade-auth', $tradeAuth) }
if ($webhook)    { $argsList += @('--webhook', $webhook) }

Write-Host "Starting watcher (poll=${Poll}ms, region=${Region})..." -ForegroundColor Green

& node @argsList
