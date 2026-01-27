Param(
    [string]$BaseDir = "infrastructure\whatsapp",
    [string]$ApiPort = "8080",
    [string]$BackendUrl = "http://localhost:8000",
    [string]$DbUrl = "postgresql://postgres:Yq7xwQpt6c@localhost:5432/evolution_api",
    [string]$ApiKey = "42247726A7F14310B30A3CA655148D32",
    [string]$InstanceName = "EXFIN",
    [string]$Mode = "", # install, update, repair
    [string]$ServiceType = "pm2" # pm2, service
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Write-Safe: Server 2012 uyumlulugu icin [Console]::WriteLine kullanir
function Write-Safe($msg, $color = "White") {
    try {
        [Console]::ResetColor()
        switch ($color) {
            "Cyan" { [Console]::ForegroundColor = [ConsoleColor]::Cyan }
            "Green" { [Console]::ForegroundColor = [ConsoleColor]::Green }
            "Yellow" { [Console]::ForegroundColor = [ConsoleColor]::Yellow }
            "Red" { [Console]::ForegroundColor = [ConsoleColor]::Red }
            "White" { [Console]::ForegroundColor = [ConsoleColor]::White }
            "Gray" { [Console]::ForegroundColor = [ConsoleColor]::Gray }
            default { [Console]::ForegroundColor = [ConsoleColor]::White }
        }
        [Console]::WriteLine($msg)
        [Console]::ResetColor()
    }
    catch {
        Write-Output $msg
    }
}

Write-Safe "============================" "Cyan"
Write-Safe "EXFIN WhatsApp Setup Module" "Cyan"
Write-Safe "============================" "Cyan"

# --- FUNCTIONS ---

function Show-Menu {
    Write-Safe "`nLutfen bir islem secin:" "White"
    Write-Safe "1) Sifirdan Kurulum (Fresh Install)" "Green"
    Write-Safe "2) Guncelle (Update) - Kodlari ceker ve servisi yeniler" "Yellow"
    Write-Safe "3) Onar (Repair) - Her seyi siler ve bastan kurar" "Blue"
    Write-Safe "4) Cikis" "Cyan"
    
    $choice = Read-Host "`nSeciminiz (1-4)"
    return $choice
}

function Setup-Environment {
    Write-Safe "[*] Sistem kontrolu yapiliyor..." "Yellow"
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
    Write-Safe "[*] Yapilandirma dosyasi (.env) olusturuluyor..." "Yellow"
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
    [System.IO.File]::WriteAllText((Join-Path (Get-Location) ".env"), $EnvContent, (New-Object System.Text.UTF8Encoding($false)))
}

function Register-Windows-Service {
    Write-Host "[*] Windows Servisi kaydediliyor (NSSM)..." -ForegroundColor Yellow
    
    $nssm = Get-Command nssm -ErrorAction SilentlyContinue
    if (!$nssm) {
        Write-Safe "NSSM bulunamadi, indiriliyor..."
        $nssmPath = Join-Path (Get-Location) "nssm.exe"
        if (!(Test-Path $nssmPath)) {
            Invoke-WebRequest -Uri "https://nssm.cc/release/nssm-2.24.zip" -OutFile "nssm.zip"
            # Use tar for extraction to bypass PowerShell Constrained Language Mode restrictions
            New-Item -Path "nssm_temp" -ItemType Directory -Force | Out-Null
            tar -xf "nssm.zip" -C "nssm_temp"
            Copy-Item "nssm_temp\nssm-2.24\win64\nssm.exe" -Destination $nssmPath -Force
            Remove-Item "nssm.zip", "nssm_temp" -Recurse -Force
        }
    }
    else {
        $nssmPath = $nssm.Source
    }

    $serviceName = "Exfin_WhatsAppService"
    $nodePath = Get-Command node | Select-Object -ExpandProperty Source
    $scriptRoot = Get-Location
    $entryPoint = Join-Path $scriptRoot "dist\main.js"

    # Stop and remove existing if any
    & $nssmPath stop $serviceName 2>$null
    & $nssmPath remove $serviceName confirm 2>$null
    
    $scriptRoot = (Get-Location).Path
    $entryPoint = Join-Path $scriptRoot "dist\main.js"

    # Install and set up
    Write-Safe "[*] NSSM ile servis kaydediliyor..." "Yellow"
    & $nssmPath install $serviceName "$nodePath" "$entryPoint"
    & $nssmPath set $serviceName AppDirectory "$scriptRoot"
    & $nssmPath set $serviceName Description "EXFIN ALL WhatsApp Service"
    & $nssmPath set $serviceName Start SERVICE_AUTO_START
    
    # Logging
    & $nssmPath set $serviceName AppStdout (Join-Path $scriptRoot "service_stdout.log")
    & $nssmPath set $serviceName AppStderr (Join-Path $scriptRoot "service_stderr.log")
    
    # Permissions
    Write-Safe "[*] Klasor izinleri duzenleniyor (SYSTEM account)..." "Yellow"
    icacls $scriptRoot /grant "SYSTEM:(OI)(CI)F" /T /C /Q
    
    Write-Safe "[*] Servis baslatiliyor..." "Yellow"
    & $nssmPath start $serviceName

    Write-Safe "`n[BASARILI] WhatsApp Windows Servisi ($serviceName) kuruldu ve baslatildi. ✅" "Green"
    Write-Safe "[BILGI] Loglar: $scriptRoot\service_stdout.log" "Gray"
}

function Start-API-Service {
    if ($ServiceType -eq "") {
        Write-Safe "`nServis Baslatma Tercihi:" "White"
        Write-Safe "1) PM2 ile Baslat (Onerilen - Konsol Yonetimi Kolay)" "Yellow"
        Write-Safe "2) Native Windows Servisi Olarak Kaydet (Sistem Seviyesi - sc.exe)" "Blue"
        
        $choice = Read-Host "Seciminiz (1-2)"
        if ($choice -eq "2") { $ServiceType = "service" } else { $ServiceType = "pm2" }
    }
    
    if ($ServiceType -eq "service") {
        Register-Windows-Service
    }
    else {
        Write-Safe "[*] Servis baslatiliyor (PM2)..." "Yellow"
        $pm2 = Get-Command pm2 -ErrorAction SilentlyContinue
        if (!$pm2) {
            Write-Safe "PM2 bulunamadi, yukleniyor..."
            npm install -g pm2
            # Refresh path to find pm2
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
            $pm2 = Get-Command pm2 -ErrorAction SilentlyContinue
        }
        
        $pm2Path = if ($pm2) { $pm2.Source } else { "pm2" }
        $scriptRoot = (Get-Location).Path
        $entryPoint = Join-Path $scriptRoot "dist\main.js"
 
        & $pm2Path delete exfin-whatsapp-api 2>$null
        & $pm2Path start "$entryPoint" --name exfin-whatsapp-api --cwd "$scriptRoot"
        & $pm2Path save
        Write-Safe "`n[BASARILI] Evolution API port $ApiPort uzerinde calisiyor (PM2). ✅" "Green"
    }
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
        Write-Safe "`n>>> SIFIRDAN KURULUM BASLATILDI <<<" "Green"
        if (Test-Path "package.json") {
            Write-Safe "[*] Kodlar zaten mevcut, guncelleniyor..." "Yellow"
            git fetch --all
            git reset --hard origin/main
        }
        else {
            git clone https://github.com/EvolutionAPI/evolution-api.git .
        }
        Create-EnvFile
        npm install
        npm run db:generate
        npm run build
        npm run db:deploy:win
        Start-API-Service
    }
    
    "update" {
        Write-Safe "`n>>> GUNCELLEME BASLATILDI <<<" "Yellow"
        git pull
        Create-EnvFile
        npm install
        npm run build
        Start-API-Service
    }
    
    "repair" {
        Write-Safe "`n>>> ONARIM BASLATILDI <<<" "Blue"
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
