<#
    EXFIN WhatsApp Deployment Script
    Usage: irm setup.ps1 | iex
#>

Param(
    [string]$BaseDir = "infrastructure\whatsapp",
    [string]$ApiPort = "8081", # Internal Engine Port
    [string]$DashboardPort = "8001", # Public Dashboard Port
    [string]$BackendUrl = "http://localhost:8000",
    [string]$DbUrl = "postgresql://postgres:Yq7xwQpt6c@localhost:5432/evolution_api",
    [string]$ApiKey = "42247726A7F14310B30A3CA655148D32",
    [string]$InstanceName = "EXFIN"
)

Write-Host "==============================" -ForegroundColor Cyan
Write-Host "WhatsApp Api Reporter (BerqenasCloud Api Services)" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan

# 1. Environment Check
if (!(Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Error "Node.js is not installed! Please install Node.js first."
    return
}

# 2. Directory Setup
if (!(Test-Path $BaseDir)) {
    New-Item -Path $BaseDir -ItemType Directory -Force
}

$EngineDir = Join-Path $BaseDir "engine"
$ManagerDir = Join-Path $BaseDir "manager"

if (!(Test-Path $EngineDir)) { New-Item -Path $EngineDir -ItemType Directory -Force }
if (!(Test-Path $ManagerDir)) { New-Item -Path $ManagerDir -ItemType Directory -Force }

# --- PART 1: ENGINE SETUP ---
Write-Host "`n[1/6] Preparing BerqenasCloud Engine (Internal Port: $ApiPort)..." -ForegroundColor Yellow
Set-Location $EngineDir

if (Test-Path "$EngineDir\.git") {
    Write-Host "Existing engine detected. Syncing..." -ForegroundColor Gray
    try {
        git fetch --all
        git reset --hard origin/main
    }
    catch {
        Remove-Item -Path "$EngineDir\*" -Recurse -Force
        git clone https://github.com/EvolutionAPI/evolution-api.git .
    }
}
else {
    git clone https://github.com/EvolutionAPI/evolution-api.git .
}

Write-Host "[2/6] Configuring Engine Environment..." -ForegroundColor Yellow
$EnvContent = @"
SERVER_NAME=$InstanceName
SERVER_TYPE=http
SERVER_PORT=$ApiPort
SERVER_URL=http://localhost:$ApiPort

DATABASE_PROVIDER=postgresql
DATABASE_CONNECTION_URI=$DbUrl
DATABASE_CONNECTION_CLIENT_NAME=evolution

# Security
AUTHENTICATION_API_KEY=$ApiKey

# Cache & Logs
CACHE_REDIS_ENABLED=false
CACHE_LOCAL_ENABLED=true
LOG_LEVEL=ERROR,WARN,INFO
LANGUAGE=en-US

# Manager Integration
qrcode=true
"@
$EnvContent | Out-File -FilePath ".env" -Encoding utf8

Write-Host "[3/6] Building Engine..." -ForegroundColor Yellow
npm install
npm run db:generate
npm run build
npm run db:deploy:win

# --- PART 2: MANAGER SETUP ---
Write-Host "`n[4/6] Preparing BerqenasCloud Dashboard (Public Port: $DashboardPort)..." -ForegroundColor Yellow
Set-Location $ManagerDir

if (Test-Path "$ManagerDir\.git") {
    Write-Host "Existing manager detected. Syncing..." -ForegroundColor Gray
    try {
        git fetch --all
        git reset --hard origin/main
    }
    catch {
        Remove-Item -Path "$ManagerDir\*" -Recurse -Force
        git clone https://github.com/EvolutionAPI/evolution-manager.git .
    }
}
else {
    git clone https://github.com/EvolutionAPI/evolution-manager.git .
}

Write-Host "[5/6] Configuring Dashboard Environment..." -ForegroundColor Yellow
$ManagerEnv = @"
VITE_SERVER_URL=http://localhost:$ApiPort
VITE_API_KEY=$ApiKey
"@
$ManagerEnv | Out-File -FilePath ".env" -Encoding utf8

Write-Host "[6/6] Building Dashboard..." -ForegroundColor Yellow
npm install
npm run build

# --- PART 3: STARTUP ---
Write-Host "`n[FINAL] Starting Services..." -ForegroundColor Yellow

# Helper to find PM2
$PM2 = "pm2"
if (!(Get-Command pm2 -ErrorAction SilentlyContinue)) {
    Write-Host "PM2 not found in PATH. Checking npm prefix..."
    npm install -g pm2
    $NpmPrefix = npm config get prefix
    $PM2 = "$NpmPrefix\pm2.cmd"
}

# Ensure Serve is installed
if (!(Get-Command serve -ErrorAction SilentlyContinue)) {
    npm install -g serve
}

# Start Engine
& $PM2 delete exfin-whatsapp-api 2>$null # Delete legacy if exists
& $PM2 delete exfin-wa-engine 2>$null
& $PM2 start "$EngineDir\dist\main.js" --name exfin-wa-engine

# Start Manager
& $PM2 delete exfin-wa-dashboard 2>$null
& $PM2 start "serve" --name exfin-wa-dashboard -- -s "$ManagerDir\dist" -l $DashboardPort --single

& $PM2 save

Write-Host "`n==============================================" -ForegroundColor Green
Write-Host " INSTALLATION COMPLETE ✅" -ForegroundColor Green
Write-Host " - Dashboard: http://localhost:$DashboardPort (Use this!)" -ForegroundColor Green
Write-Host " - API Engine: http://localhost:$ApiPort (Internal)" -ForegroundColor Yellow
Write-Host "==============================================" -ForegroundColor Green
