Param(
    [string]$BaseDir = "infrastructure\whatsapp",
    [string]$ApiPort = "8080",
    [string]$BackendUrl = "http://localhost:8000",
    [string]$DbUrl = "postgresql://postgres:Yq7xwQpt6c@localhost:5432/evolution_api",
    [string]$ApiKey = "42247726A7F14310B30A3CA655148D32",
    [string]$InstanceName = "EXFIN",
    [string]$Mode = "" # install, update, repair
)

Write-Host "============================" -ForegroundColor Cyan
Write-Host "EXFIN WhatsApp Setup Module" -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan

# --- FUNCTIONS ---

function Show-Menu {
    Write-Host "`nLütfen bir işlem seçin:" -ForegroundColor White
    Write-Host "1) Sıfırdan Kurulum (Fresh Install)" -ForegroundColor Green
    Write-Host "2) Güncelle (Update) - Kodları çeker ve servisi yeniler" -ForegroundColor Yellow
    Write-Host "3) Onar (Repair) - Her şeyi siler ve baştan kurar" -ForegroundColor Blue
    Write-Host "4) Çıkış" -ForegroundColor Cyan
    
    $choice = Read-Host "`nSeçiminiz (1-4)"
    return $choice
}

function Setup-Environment {
    Write-Host "[*] Sistem kontrolü yapılıyor..." -ForegroundColor Yellow
    if (!(Get-Command node -ErrorAction SilentlyContinue)) {
        Write-Error "Node.js bulunamadı! Lütfen önce Node.js kurun."
        return $false
    }
    
    if (!(Test-Path $BaseDir)) {
        New-Item -Path $BaseDir -ItemType Directory -Force
    }
    Set-Location $BaseDir
    return $true
}

function Create-EnvFile {
    Write-Host "[*] Yapılandırma dosyası (.env) oluşturuluyor..." -ForegroundColor Yellow
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

# Client Name
CONFIG_SESSION_PHONE_CLIENT=$InstanceName
CONFIG_SESSION_PHONE_NAME=Chrome

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
}

function Start-API-Service {
    Write-Host "[*] Servis başlatılıyor (PM2)..." -ForegroundColor Yellow
    $pm2 = Get-Command pm2 -ErrorAction SilentlyContinue
    if (!$pm2) {
        Write-Host "PM2 bulunamadı, yükleniyor..."
        npm install -g pm2
        $pm2Path = "$(npm config get prefix)\pm2.cmd"
    }
    else {
        $pm2Path = $pm2.Source
    }

    & $pm2Path delete exfin-whatsapp-api 2>$null
    & $pm2Path start dist/main.js --name exfin-whatsapp-api
    & $pm2Path save
    Write-Host "`n[BAŞARILI] Evolution API port $ApiPort üzerinde çalışıyor. ✅" -ForegroundColor Green
}

# --- MAIN LOGIC ---

if ($Mode -eq "") {
    $ModeChoice = Show-Menu
    switch ($ModeChoice) {
        "1" { $Mode = "install" }
        "2" { $Mode = "update" }
        "3" { $Mode = "repair" }
        default { return }
    }
}

if (!(Setup-Environment)) { return }

switch ($Mode) {
    "install" {
        Write-Host "`n>>> SIFIRDAN KURULUM BAŞLATILDI <<<" -ForegroundColor Green
        git clone https://github.com/EvolutionAPI/evolution-api.git .
        Create-EnvFile
        npm install
        npm run db:generate
        npm run build
        npm run db:deploy:win
        Start-API-Service
    }
    
    "update" {
        Write-Host "`n>>> GÜNCELLEME BAŞLATILDI <<<" -ForegroundColor Yellow
        git pull
        Create-EnvFile
        npm install
        npm run build
        Start-API-Service
    }
    
    "repair" {
        Write-Host "`n>>> ONARIM BAŞLATILDI <<<" -ForegroundColor Blue
        # Stop service first
        pm2 stop exfin-whatsapp-api 2>$null
        
        # Pull latest code
        git fetch --all
        git reset --hard origin/main
        
        Create-EnvFile
        npm install
        npm run db:generate
        npm run build
        npm run db:deploy:win
        Start-API-Service
    }
}
