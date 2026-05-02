param(
    [string]$ChromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe",
    [string]$UserDataDir = "",
    [int]$Port = 9222,
    [switch]$NewWindow
)

$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if ([string]::IsNullOrWhiteSpace($UserDataDir)) {
    $UserDataDir = Join-Path $projectRoot "runtime\chrome-workbench\profile"
}

New-Item -ItemType Directory -Force -Path $UserDataDir | Out-Null

if (-not (Test-Path $ChromePath)) {
    Write-Error "Chrome not found: $ChromePath"
    exit 1
}

$versionUrl = "http://127.0.0.1:$Port/json/version"
try {
    $resp = Invoke-WebRequest -UseBasicParsing -Uri $versionUrl -TimeoutSec 2
    if ($resp.StatusCode -eq 200) {
        Write-Host "CDP already available at $versionUrl"
        Write-Host "UserDataDir: $UserDataDir"
        exit 0
    }
} catch {
}

$args = @(
    "--remote-debugging-port=$Port",
    "--user-data-dir=$UserDataDir",
    "--no-first-run",
    "--no-default-browser-check"
)

if ($NewWindow) {
    $args += "--new-window"
}

Start-Process -FilePath $ChromePath -ArgumentList $args | Out-Null
Write-Host "Chrome launched."
Write-Host "CDP endpoint: $versionUrl"
Write-Host "UserDataDir: $UserDataDir"
Write-Host "Please log in manually and keep this browser open."
