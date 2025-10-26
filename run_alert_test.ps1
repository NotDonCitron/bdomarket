# PowerShell wrapper to run alert verification test with proper UTF-8
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

Set-Location -Path $PSScriptRoot
& ".\.venv\Scripts\python.exe" "test_alert_verification.py"
