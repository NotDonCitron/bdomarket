# PowerShell runner for Auto-Buy Verification (safe defaults)
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

Set-Location -Path $PSScriptRoot

# Safe defaults: dry-run, 3 minutes timeout, quantity 1, auto price cap (base*1.10)
& ".\.venv\Scripts\python.exe" "test_autobuy_blackstone.py" `
  --item-id 16001 `
  --interval 1.0 `
  --quantity 1 `
  --timeout 180

Write-Host "\nDone. To execute a live buy, run:" -ForegroundColor Yellow
Write-Host "  .\.venv\Scripts\python.exe test_autobuy_blackstone.py --confirm --item-id 16001 --quantity 1 --price-cap 220000 --timeout 120" -ForegroundColor Yellow
