$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidFile = Join-Path $projectRoot '.run\pids.json'
if (-not (Test-Path -LiteralPath $pidFile)) {
    Write-Host 'No CinemaOS process file was found.'
    exit 0
}
$saved = Get-Content -LiteralPath $pidFile -Raw | ConvertFrom-Json
foreach ($processId in @($saved.backend, $saved.frontend)) {
    if ($processId -and (Get-Process -Id $processId -ErrorAction SilentlyContinue)) {
        Stop-Process -Id $processId
    }
}
Remove-Item -LiteralPath $pidFile
Write-Host 'CinemaOS stopped.' -ForegroundColor Green
