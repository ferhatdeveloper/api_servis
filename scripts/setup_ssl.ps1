
# Script: setup_ssl.ps1
# Purpose: Generate SSL Certificates and configure both PostgreSQL and API Service
# Usage: irm ... | iex

Write-Host ">>> EXFIN OPS System-Wide SSL Setup <<<" -ForegroundColor Cyan

# 1. Detect Directories
$ProjectDir = "d:\Developer\App\EXFIN_OPS\backend"
$ScriptsDir = Join-Path $ProjectDir "scripts"
$EnvFile = Join-Path $ProjectDir ".env"
$PythonExe = Join-Path $ProjectDir "venv\Scripts\python.exe"

# 2. Check Python
if (-not (Test-Path $PythonExe)) {
    Write-Host "Error: Virtual environment python not found at $PythonExe" -ForegroundColor Red
    exit 1
}

# 3. Generate Certificates
Write-Host "> Generating SSL Certificates..." -ForegroundColor Yellow
$CertScript = Join-Path $ScriptsDir "generate_cert.py"
if (-not (Test-Path $CertScript)) {
    Write-Host "Error: $CertScript not found." -ForegroundColor Red
    exit 1
}

# Run python script to generate certs (it returns paths, but we know where they land)
# We can just rely on the script updating the .env or just use known paths
& $PythonExe -c "import sys; sys.path.insert(0, r'$ScriptsDir'); import generate_cert; print(generate_cert.generate_self_signed_cert())"

# Read paths from .env to be sure
$CertFile = ""
$KeyFile = ""

if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match "SSL_CERT_FILE=(.*)") { $CertFile = $matches[1] }
        if ($_ -match "SSL_KEY_FILE=(.*)") { $KeyFile = $matches[1] }
    }
}

if (-not $CertFile -or -not $KeyFile) {
    Write-Host "Error: Could not determine certificate paths from .env" -ForegroundColor Red
    exit 1
}

Write-Host "  Cert: $CertFile" -ForegroundColor Gray
Write-Host "  Key:  $KeyFile" -ForegroundColor Gray

# Check for PFX (IIS)
$CertDir = Split-Path $CertFile
$PfxFile = Join-Path $CertDir "cert.pfx"
if (Test-Path $PfxFile) {
    Write-Host "  PFX:  $PfxFile (For IIS, Pass: 123456)" -ForegroundColor Cyan
}

# 4. Configure PostgreSQL
Write-Host "> Configuring PostgreSQL..." -ForegroundColor Yellow
$PostgresService = Get-Service -Name "postgresql-x64-16" -ErrorAction SilentlyContinue
if (-not $PostgresService) {
    # Try finding any postgres service
    $PostgresService = Get-Service | Where-Object { $_.Name -like "postgresql*" -and $_.Status -eq 'Running' } | Select-Object -First 1
}

if ($PostgresService) {
    Write-Host "  Found PostgreSQL Service: $($PostgresService.Name)" -ForegroundColor Green
    
    # Try to find data directory via registry or standard paths
    # Hardcoded fallback based on earlier find_by_name result
    $DataDir = "C:\Program Files\PostgreSQL\16\data" 
    
    if (-not (Test-Path $DataDir)) {
        Write-Host "  Warning: Data directory $DataDir not found. Skipping auto-config." -ForegroundColor Yellow
    }
    else {
        $ConfFile = Join-Path $DataDir "postgresql.conf"
        $HbaFile = Join-Path $DataDir "pg_hba.conf"
        
        # Copy certs to DataDir (Postgres user needs read access, easiest is to put them in data dir)
        $PgCert = Join-Path $DataDir "server.crt"
        $PgKey = Join-Path $DataDir "server.key"
        
        Copy-Item -Path $CertFile -Destination $PgCert -Force
        Copy-Item -Path $KeyFile -Destination $PgKey -Force
        
        # Update postgresql.conf
        $ConfContent = Get-Content $ConfFile
        $SSLConfigured = $false
        $NewConf = $ConfContent | ForEach-Object {
            if ($_ -match "^#?ssl\s*=") { "ssl = on"; $SSLConfigured = $true }
            elseif ($_ -match "^#?ssl_cert_file\s*=") { "ssl_cert_file = 'server.crt'" }
            elseif ($_ -match "^#?ssl_key_file\s*=") { "ssl_key_file = 'server.key'" }
            else { $_ }
        }
        
        if (-not $SSLConfigured) {
            $NewConf += "ssl = on"
            $NewConf += "ssl_cert_file = 'server.crt'"
            $NewConf += "ssl_key_file = 'server.key'"
        }
        
        $NewConf | Set-Content $ConfFile
        Write-Host "  Updated postgresql.conf" -ForegroundColor Green
        
        # Update pg_hba.conf (Enable hostssl)
        # Check if hostssl exists
        $HbaContent = Get-Content $HbaFile
        $HasHostSSL = $HbaContent | Where-Object { $_ -match "^hostssl" }
        
        if (-not $HasHostSSL) {
            Add-Content -Path $HbaFile -Value "hostssl all             all             0.0.0.0/0               scram-sha-256"
            Write-Host "  Updated pg_hba.conf (Added hostssl rule)" -ForegroundColor Green
        }
        
        # Restart PostgreSQL
        Write-Host "  Restarting PostgreSQL Service..." -ForegroundColor Yellow
        Restart-Service -Name $PostgresService.Name -Force
        Write-Host "  PostgreSQL Restarted." -ForegroundColor Green
    }
}
else {
    Write-Host "  Warning: PostgreSQL Service not found." -ForegroundColor Yellow
}

# 5. Restart API Service
Write-Host "> Restarting EXFIN OPS API Service..." -ForegroundColor Yellow
$ApiService = Get-Service -Name "Exfin_ApiService" -ErrorAction SilentlyContinue
if ($ApiService) {
    Restart-Service -Name "Exfin_ApiService" -Force
    Write-Host "  API Service Restarted." -ForegroundColor Green
}
else {
    Write-Host "  API Service not installed or found." -ForegroundColor Gray
}

Write-Host ">>> SSL Configuration Complete! <<<" -ForegroundColor Cyan
Write-Host "Connect to Postgres using: user, database, SSL=Required"
