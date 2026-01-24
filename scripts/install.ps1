# EXFIN OPS API - Akıllı Kurulum ve Güncelleme Scripti
# Kullanım: irm bit.ly/opsapi | iex

$ErrorActionPreference = "Stop"

# CRITICAL: Force UTF-8 Terminal and Environment
Try {
    chcp 65001 >$null
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    [Console]::InputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
    $env:PYTHONIOENCODING = "utf-8"
}
Catch { }

# 0. Cleanup / Policy Fix Argument Handling
# Fallback support for Invoke-Expression (iex) which doesn't support -Arguments
$OPS_MODE = if ($args[0]) { $args[0] } else { $env:OPS_ARG }

if ($OPS_MODE -eq "cleanup") {
    Write-Host "[BİLGİ] Python Temizleme Aracı başlatılıyor..." -ForegroundColor Yellow
    # Cache-busting download
    $Id = Get-Random
    $CleanupUrl = "https://raw.githubusercontent.com/ferhatdeveloper/api_servis/main/scripts/cleanup_python.ps1?v=$Id"
    $CleanupPath = Join-Path $env:TEMP "cleanup_python.ps1"
    Invoke-WebRequest -Uri $CleanupUrl -OutFile $CleanupPath -Headers @{"Cache-Control" = "no-cache" } -ErrorAction SilentlyContinue
    if (Test-Path $CleanupPath) {
        & $CleanupPath
    }
    else {
        Write-Host "[HATA] Temizleme aracı indirilemedi." -ForegroundColor Red
    }
    return
}

if ($OPS_MODE -eq "fix-policy") {
    Write-Host "[BİLGİ] Kurulum Politikası Düzeltici başlatılıyor..." -ForegroundColor Yellow
    # Cache-busting download
    $Id = Get-Random
    $FixUrl = "https://raw.githubusercontent.com/ferhatdeveloper/api_servis/main/scripts/fix_installation_policy.ps1?v=$Id"
    $FixPath = Join-Path $env:TEMP "fix_policy.ps1"
    Invoke-WebRequest -Uri $FixUrl -OutFile $FixPath -Headers @{"Cache-Control" = "no-cache" } -ErrorAction SilentlyContinue
    if (Test-Path $FixPath) {
        & $FixPath
    }
    else {
        Write-Host "[HATA] Düzeltme aracı indirilemedi." -ForegroundColor Red
    }
    return
}

$RepoUrl = "https://github.com/ferhatdeveloper/api_servis.git"

$DefaultDir = "C:\ExfinApi"

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "   EXFIN OPS API - ONE-LINE INSTALLER v5.5" -ForegroundColor Cyan
Write-Host "==========================================`n" -ForegroundColor Cyan

# 1. Yönetici Kontrolü
if (!([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "[HATA] Lütfen PowerShell'i 'Yönetici Olarak' çalıştırın!" -ForegroundColor Red
    return
}

# 2. Çalışma Dizini Belirleme
$TargetDir = $DefaultDir 

if (!(Test-Path $TargetDir)) {
    Write-Host "[BİLGİ] Klasör oluşturuluyor: $TargetDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $TargetDir | Out-Null
}

Set-Location $TargetDir

# 3. Git Kontrolü ve İndirme
if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "[UYARI] Git bulunamadı! Repo ZIP olarak indiriliyor..." -ForegroundColor Yellow
    $ZipPath = Join-Path $TargetDir "repo.zip"
    Invoke-WebRequest -Uri "$RepoUrl/archive/refs/heads/main.zip" -OutFile $ZipPath
    Expand-Archive -Path $ZipPath -DestinationPath $TargetDir -Force
    # Move files from subdirectory to root if needed
    $SubDir = Get-ChildItem -Path $TargetDir -Directory | Where-Object { $_.Name -like "*-main" }
    if ($SubDir) {
        Move-Item -Path "$($SubDir.FullName)\*" -Destination $TargetDir -Force
        Remove-Item -Path $SubDir.FullName -Recurse -Force
    }
    Remove-Item -Path $ZipPath -Force
}
else {
    if (!(Test-Path ".git")) {
        Write-Host "[BİLGİ] Repo klonlanıyor..." -ForegroundColor Yellow
        git clone $RepoUrl .
    }
    else {
        Write-Host "[BİLGİ] Mevcut depo güncelleniyor..." -ForegroundColor Yellow
        git fetch origin | Out-Null
        git reset --hard origin/main | Out-Null
    }
}

# 4. Python Kontrolü
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[HATA] Python bulunamadı!" -ForegroundColor Red
    
    $Arch = $env:PROCESSOR_ARCHITECTURE
    $PyUrl = "https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe"
    if ($Arch -eq "ARM64") {
        $PyUrl = "https://www.python.org/ftp/python/3.12.8/python-3.12.8-arm64.exe"
    }

    Write-Host "[BİLGİ] Sistem Mimarisi: $Arch" -ForegroundColor Yellow
    Write-Host "[BİLGİ] Önerilen Sürüm: Python 3.12.8 ($Arch)" -ForegroundColor Cyan
    Write-Host "[BİLGİ] İndirme Linki: $PyUrl" -ForegroundColor Cyan
    
    Start-Process $PyUrl
    return
}


$PyVer = python --version 2>&1
Write-Host "[BİLGİ] Mevcut $PyVer tespit edildi." -ForegroundColor Yellow

# Parse version (e.g. "Python 3.7.7" -> 307)
$VerClean = $PyVer -replace '[^0-9.]', ''
$VerParts = $VerClean.Split('.')
$Major = [int]$VerParts[0]
$Minor = [int]$VerParts[1]

if ($Major -lt 3 -or ($Major -eq 3 -and $Minor -lt 10)) {
    Write-Host "[HATA] Mevcut Python sürümünüz ($VerClean) çok eski!" -ForegroundColor Red
    Write-Host "[BİLGİ] Bu uygulama için en az Python 3.10 gereklidir." -ForegroundColor Cyan
    Write-Host "[ÖNERİ] Eğer kurulum 'Sistem Politikası' hatasıyla (0x80070659) engellenirse şu komutu çalıştırın:" -ForegroundColor Yellow
    Write-Host ">>> `$env:OPS_ARG='fix-policy'; irm bit.ly/opsapi | iex" -ForegroundColor Magenta
    Write-Host "[BİLGİ] Lütfen Python 3.12.8 yükleyin (Otomatik kurulum başlatılıyor...)" -ForegroundColor Cyan
    
    $Arch = $env:PROCESSOR_ARCHITECTURE
    $PyUrl = "https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe"
    if ($Arch -eq "ARM64") { $PyUrl = "https://www.python.org/ftp/python/3.12.8/python-3.12.8-arm64.exe" }
    
    $PyInstallerPath = Join-Path $env:TEMP "python_installer.exe"
    Invoke-WebRequest -Uri $PyUrl -OutFile $PyInstallerPath
    
    # 4.1 Unblock and Install
    Unblock-File -Path $PyInstallerPath -ErrorAction SilentlyContinue
    Write-Host "[İŞLEM] Python kuruluyor... Lütfen bekleyin." -ForegroundColor Yellow
    
    # Precise arguments for silent install to bypass TARGETDIR and Policy errors
    $InstallArgs = @(
        "/quiet",
        "InstallAllUsers=1",
        "PrependPath=1",
        "Include_test=0"
    )
    
    $proc = Start-Process -FilePath $PyInstallerPath -ArgumentList $InstallArgs -Wait -PassThru
    
    if ($proc.ExitCode -eq 0) {
        Write-Host "[BAŞARILI] Python kuruldu. Terminali yenilemeniz gerekebilir." -ForegroundColor Green
    }
    else {
        Write-Host "[HATA] Python kurulumu hata koduyla bitti: $($proc.ExitCode)" -ForegroundColor Red
        Write-Host "[BİLGİ] Eğer sorun devam ediyorsa lütfen 'Politika Düzeltici'yi tekrar çalıştırın (Güncellendi v2.2)." -ForegroundColor Yellow
    }
    return
}

if ($PyVer -like "*3.13*") {
    Write-Host "[UYARI] Python 3.13 kullanıyorsunuz. Bu sürüm bazı kütüphanelerde derleme (build) hatalarına neden olabilir." -ForegroundColor Yellow
    Write-Host "[BİLGİ] Eğer hata alırsanız Python 3.12.x kurmanızı öneririz." -ForegroundColor Cyan
}



# 5. Sanal Ortam ve Bağımlılıklar
if (!(Test-Path "venv")) {
    Write-Host "[BİLGİ] Sanal ortam oluşturuluyor..." -ForegroundColor Yellow
    python -m venv venv
}

Write-Host "[BİLGİ] Bağımlılıklar kontrol ediliyor..." -ForegroundColor Yellow
& ".\venv\Scripts\python.exe" -m pip install --upgrade pip | Out-Null
& ".\venv\Scripts\python.exe" -m pip install -r requirements.txt | Out-Null

# 6. Kurulum Tercihi
Write-Host "`n[SEÇİM] Uygulama çalışma modunu seçin:" -ForegroundColor White
Write-Host "1) Windows Servisi (Önerilen: Bilgisayar açılınca otomatik başlar, arka planda çalışır)" -ForegroundColor Cyan
Write-Host "2) Tray Uygulaması (Manuel: Saatin yanındaki simge üzerinden kontrol edilir)" -ForegroundColor Cyan
$choice = Read-Host "`nSeçiminiz (1 veya 2, Varsayılan: 1)"

if ($null -eq $choice -or $choice -eq "") { $choice = "1" }

# 7. Başlatma
if (Test-Path "start_setup.py") {
    $PythonPath = Join-Path $TargetDir "venv\Scripts\python.exe"
    $SetupScript = Join-Path $TargetDir "start_setup.py"
    
    # 7.1 Servis Adı Kontrolü (Sadece Servis modu seçildiyse)
    if ($choice -eq "1") {
        Write-Host "[BİLGİ] Windows Servisi kontrol ediliyor..." -ForegroundColor Yellow
        $SvcName = "Exfin_ApiService"
        if (Get-Service $SvcName -ErrorAction SilentlyContinue) {
            Write-Host "[UYARI] '$SvcName' adında bir servis zaten mevcut!" -ForegroundColor Yellow
            $NewName = Read-Host "Yeni servis adını girin (Boş bırakırsanız mevcut servis güncellenir)"
            if ($null -ne $NewName -and $NewName -ne "") {
                $SvcName = $NewName
                Write-Host "[BİLGİ] Yeni servis adı belirlendi: $SvcName" -ForegroundColor Cyan
                # Persist to api.db so the service knows its own name
                & $PythonPath -c "import sqlite3,os; db='api.db'; conn=sqlite3.connect(db); conn.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)'); conn.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (''ServiceName'', ?)', ('$SvcName',)); conn.commit(); conn.close()"
            }
        }
    }

    Write-Host "[BAŞARILI] Kurulum sihirbazı başlatılıyor..." -ForegroundColor Green
    # Launch start_setup.py with the choice parameter
    Start-Process -FilePath $PythonPath -ArgumentList "`"$SetupScript`" --mode $choice" -WorkingDirectory $TargetDir -WindowStyle Hidden
}
else {
    Write-Host "[HATA] start_setup.py bulunamadı!" -ForegroundColor Red
}



