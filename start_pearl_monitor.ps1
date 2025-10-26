# PowerShell wrapper to start Pearl Monitor with correct encoding
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

Set-Location -Path $PSScriptRoot
& ".\.venv\Scripts\python.exe" "pearl_monitor_bdomarket.py" "--interval" "2.0"

