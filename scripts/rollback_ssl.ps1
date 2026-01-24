
# Script: rollback_ssl.ps1
# Purpose: Revert SSL Configuration for PostgreSQL and API Service
# Usage: irm ... | iex

Write-Host ">>> EXFIN OPS SSL Rollback <<<" -ForegroundColor Red

# 1. Detect Directories
$ProjectDir = "d:\Developer\App\EXFIN_OPS\backend"
$EnvFile = Join-Path $ProjectDir ".env"

# 2. Revert PostgreSQL Config
Write-Host "> Reverting PostgreSQL Configuration..." -ForegroundColor Yellow
$PostgresService = Get-Service -Name "postgresql-x64-16" -ErrorAction SilentlyContinue
if (-not $PostgresService) {
    $PostgresService = Get-Service | Where-Object { $_.Name -like "postgresql*" -and $_.Status -eq 'Running' } | Select-Object -First 1
}

if ($PostgresService) {
    $DataDir = "C:\Program Files\PostgreSQL\16\data"
    
    if (Test-Path $DataDir) {
        $ConfFile = Join-Path $DataDir "postgresql.conf"
        $HbaFile = Join-Path $DataDir "pg_hba.conf"
        
        # Disable SSL in postgresql.conf
        if (Test-Path $ConfFile) {
            $ConfContent = Get-Content $ConfFile
            $NewConf = $ConfContent | ForEach-Object {
                if ($_ -match "^ssl\s*=\s*on") { "# ssl = on (Disabled by Rollback)" }
                elseif ($_ -match "^ssl_cert_file") { "# " + $_ }
                elseif ($_ -match "^ssl_key_file") { "# " + $_ }
                else { $_ }
            }
            $NewConf | Set-Content $ConfFile
            Write-Host "  Disabled SSL in postgresql.conf" -ForegroundColor Green
        }
        
        # Remove hostssl from pg_hba.conf
        if (Test-Path $HbaFile) {
            $HbaContent = Get-Content $HbaFile
            $NewHba = $HbaContent | Where-Object { $_ -notmatch "^hostssl.*0.0.0.0/0" }
            $NewHba | Set-Content $HbaFile
            Write-Host "  Removed hostssl rule from pg_hba.conf" -ForegroundColor Green
        }
        
        # Restart PostgreSQL
        Write-Host "  Restarting PostgreSQL Service..." -ForegroundColor Yellow
        Restart-Service -Name $PostgresService.Name -Force
        Write-Host "  PostgreSQL Restarted." -ForegroundColor Green
    }
}
else {
    Write-Host "  PostgreSQL Service not found. Skipping DB rollback." -ForegroundColor Gray
}

# 3. Revert API .env
Write-Host "> Reverting API Environment..." -ForegroundColor Yellow
if (Test-Path $EnvFile) {
    $EnvContent = Get-Content $EnvFile
    $NewEnv = $EnvContent | Where-Object { 
        $_ -notmatch "^SSL_CERT_FILE=" -and 
        $_ -notmatch "^SSL_KEY_FILE=" -and 
        $_ -notmatch "^USE_HTTPS=" 
    }
    $NewEnv | Set-Content $EnvFile
    Write-Host "  Removed SSL keys from .env" -ForegroundColor Green
}

# 4. Restart API Service
Write-Host "> Restarting EXFIN OPS API Service..." -ForegroundColor Yellow
$ApiService = Get-Service -Name "Exfin_ApiService" -ErrorAction SilentlyContinue
if ($ApiService) {
    Restart-Service -Name "Exfin_ApiService" -Force
    Write-Host "  API Service Restarted." -ForegroundColor Green
}

Write-Host ">>> Rollback Complete. System is now using HTTP. <<<" -ForegroundColor Cyan
