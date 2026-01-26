<#
    EXFIN WhatsApp Deployment Script
    Usage: irm setup.ps1 | iex
#>

Param(
    [string]$BaseDir = "infrastructure\whatsapp",
    [string]$ApiPort = "8080",
    [string]$BackendUrl = "http://localhost:8000",
    [string]$DbUrl = "postgresql://postgres:Yq7xwQpt6c@localhost:5432/evolution_api",
    [string]$ApiKey = "42247726A7F14310B30A3CA655148D32",
    [string]$InstanceName = "EXFIN"
)

Write-Host "============================" -ForegroundColor Cyan
Write-Host "EXFIN WhatsApp Setup Module" -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan

# 1. Environment Check
if (!(Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Error "Node.js is not installed! Please install Node.js first."
    return
}

# 2. Directory Setup
if (!(Test-Path $BaseDir)) {
    New-Item -Path $BaseDir -ItemType Directory -Force
}

Set-Location $BaseDir

# 3. Clone Repository
Write-Host "[1/4] Cloning Evolution API..." -ForegroundColor Yellow
git clone https://github.com/EvolutionAPI/evolution-api.git .

# 4. Configuration (.env)
Write-Host "[2/4] Configuring Environment..." -ForegroundColor Yellow
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
DATABASE_SAVE_DATA_INSTANCE=true
DATABASE_SAVE_DATA_NEW_MESSAGE=true
DATABASE_SAVE_MESSAGE_UPDATE=true
DATABASE_SAVE_DATA_CONTACTS=true
DATABASE_SAVE_DATA_CHATS=true
DATABASE_SAVE_DATA_LABELS=true
LOG_LEVEL=ERROR,WARN,INFO
LANGUAGE=en-US
"@

$EnvContent | Out-File -FilePath ".env" -Encoding utf8

# 5. Install & Build
Write-Host "[3/4] Installing dependencies & Building (This may take a while)..." -ForegroundColor Yellow
npm install
npm run db:generate
npm run build

# 6. Database Migrations
Write-Host "[4/4] Running migrations..." -ForegroundColor Yellow
npm run db:deploy:win

# 7. Start Service
if (Get-Command pm2 -ErrorAction SilentlyContinue) {
    & pm2 delete exfin-whatsapp-api
    & pm2 start dist/main.js --name exfin-whatsapp-api
    & pm2 save
}
else {
    Write-Host "PM2 not found. Installing and starting..."
    npm install -g pm2
    & $(npm config get prefix)\pm2.cmd start dist/main.js --name exfin-whatsapp-api
    & $(npm config get prefix)\pm2.cmd save
}

Write-Host "`n[SUCCESS] Evolution API is now running on port $ApiPort" -ForegroundColor Green
Write-Host "Don't forget to sync webhook in backend: $BackendUrl" -ForegroundColor Green
