# EXFIN OPS - Standalone WhatsApp Installer
# Usage: irm https://raw.githubusercontent.com/ferhatdeveloper/api_servis/main/scripts/standalone_wa.ps1 | iex

$RepoUrl = "https://raw.githubusercontent.com/ferhatdeveloper/api_servis/main/scripts/install.ps1"
$TempInstaller = Join-Path $env:TEMP "exfin_temp_installer.ps1"

Write-Host "[*] WhatsApp Kurulum Sihirbazi yukleniyor..." -ForegroundColor Cyan

try {
    Invoke-WebRequest -Uri $RepoUrl -OutFile $TempInstaller -UseBasicParsing -ErrorAction Stop
    powershell -ExecutionPolicy Bypass -File $TempInstaller "whatsapp-only"
}
finally {
    if (Test-Path $TempInstaller) { Remove-Item $TempInstaller -Force }
}
