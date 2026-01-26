Param(
    [string]$BaseDir = "infrastructure\whatsapp",
    [string]$ApiPort = "8080", 
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
if (!(Test-Path $BaseDir)) { New-Item -Path $BaseDir -ItemType Directory -Force }

$EngineDir = Join-Path $BaseDir "engine"
# Clean up potential wrong clones or old data
if (Test-Path $EngineDir) { Remove-Item -Path $EngineDir -Recurse -Force }
New-Item -Path $EngineDir -ItemType Directory -Force

Set-Location $EngineDir

# 3. Clone Repository (Evolution API v2)
Write-Host "[1/4] Cloning BerqenasCloud Engine..." -ForegroundColor Yellow
# Using the correct API repository
git clone https://github.com/EvolutionAPI/evolution-api.git .

# 4. Configuration (.env)
Write-Host "[2/4] Configuring Environment..." -ForegroundColor Yellow
$EnvContent = @"
SERVER_TYPE=http
SERVER_PORT=$ApiPort
SERVER_URL=http://localhost:$ApiPort

DATABASE_PROVIDER=postgresql
DATABASE_CONNECTION_URI=$DbUrl
DATABASE_CONNECTION_CLIENT_NAME=evolution

AUTHENTICATION_API_KEY=$ApiKey

CACHE_REDIS_ENABLED=false
CACHE_LOCAL_ENABLED=true
LOG_LEVEL=ERROR,WARN,INFO
qrcode=true
"@

$EnvContent | Out-File -FilePath ".env" -Encoding utf8

# 5. Install & Build
Write-Host "[3/4] Installing dependencies & Building..." -ForegroundColor Yellow
npm install
npm run db:generate
npm run build
npm run db:deploy

# 6. Startup
Write-Host "[4/4] Starting Service..." -ForegroundColor Yellow

# Helper to find PM2
$PM2 = "pm2"
if (!(Get-Command pm2 -ErrorAction SilentlyContinue)) {
    npm install -g pm2
    $NpmPrefix = npm config get prefix
    $PM2 = "$NpmPrefix\pm2.cmd"
}

# Cleanup old processes including dashboard
& $PM2 delete exfin-whatsapp-api 2>$null
& $PM2 delete exfin-wa-dashboard 2>$null
& $PM2 delete exfin-wa-engine 2>$null

# Start Engine
& $PM2 start dist/main.js --name exfin-wa-engine
& $PM2 save

Write-Host "`n[SUCCESS] BerqenasCloud WhatsApp Api running on port $ApiPort" -ForegroundColor Green
Write-Host "Use http://localhost:$ApiPort to access the API." -ForegroundColor Green
