# EXFIN OPS API - Akıllı Kurulum ve Güncelleme Scripti
# Kullanım: irm bit.ly/opsapi | iex

$ErrorActionPreference = "Stop"

# Force UTF-8 Terminal and Output
chcp 65001 >$null
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

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
    Write-Host "[BİLGİ] Lütfen Python 3.12.8 yükleyin (İndirme başlatılıyor...)" -ForegroundColor Cyan
    
    $Arch = $env:PROCESSOR_ARCHITECTURE
    $PyUrl = "https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe"
    if ($Arch -eq "ARM64") { $PyUrl = "https://www.python.org/ftp/python/3.12.8/python-3.12.8-arm64.exe" }
    
    Start-Process $PyUrl
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
    
    Write-Host "[BAŞARILI] Kurulum sihirbazı başlatılıyor..." -ForegroundColor Green
    # Launch start_setup.py with the choice parameter
    Start-Process -FilePath $PythonPath -ArgumentList "`"$SetupScript`" --mode $choice" -WorkingDirectory $TargetDir -WindowStyle Hidden
}
else {
    Write-Host "[HATA] start_setup.py bulunamadı!" -ForegroundColor Red
}



