# fix_wsa_crash.ps1
# Fix for WSA GApps crashing (Issue #593) - English version for encoding stability

$WsaPath = "C:\WSA"
$WsaClientPath = "C:\WSA\WSA_2407.40000.4.0_x64\WsaClient\WsaClient.exe"

Write-Host "--- Fixing WSA Crash Issue (Issue #593) ---" -ForegroundColor Cyan

# 1. Disable CFG (Control Flow Guard)
if (Test-Path $WsaClientPath) {
    Write-Host "[1/2] Disabling CFG for WsaClient.exe..." -ForegroundColor Yellow
    Set-ProcessMitigation -Name WsaClient.exe -Disable CFG
    Write-Host "CFG disabled successfully." -ForegroundColor Green
} else {
    Write-Warning "WsaClient.exe not found at $WsaClientPath"
}

# 2. Add Windows Defender Exclusion
Write-Host "[2/2] Adding $WsaPath to Windows Defender Exclusion..." -ForegroundColor Yellow
try {
    Add-MpPreference -ExclusionPath $WsaPath
    Write-Host "Exclusion added successfully." -ForegroundColor Green
} catch {
    Write-Error "Failed to add exclusion. Please ensure you are running as Administrator."
}

Write-Host "`nFix complete. Please try to run WSA again or click 'Manage developer settings'." -ForegroundColor Cyan
