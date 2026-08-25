$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $projectRoot
& '.\.venv\Scripts\python.exe' -m uvicorn backend.api:app --host 127.0.0.1 --port 8000 --reload
