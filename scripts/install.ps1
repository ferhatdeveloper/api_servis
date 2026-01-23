# EXFIN OPS API - Akıllı Kurulum ve Güncelleme Scripti
# Kullanım: irm bit.ly/opsapi | iex

$ErrorActionPreference = "Stop"
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
    Write-Host "[HATA] Python bulunamadı! Lütfen Python 3.10+ yükleyin." -ForegroundColor Red
    Start-Process "https://www.python.org/downloads/"
    return
}

# 5. Sanal Ortam ve Bağımlılıklar
if (!(Test-Path "venv")) {
    Write-Host "[BİLGİ] Sanal ortam oluşturuluyor..." -ForegroundColor Yellow
    python -m venv venv
}

Write-Host "[BİLGİ] Bağımlılıklar kontrol ediliyor..." -ForegroundColor Yellow
& ".\venv\Scripts\python.exe" -m pip install --upgrade pip | Out-Null
& ".\venv\Scripts\python.exe" -m pip install -r requirements.txt | Out-Null

# 6. Sihirbazı Başlat
if (Test-Path "start_setup.py") {
    Write-Host "[BAŞARILI] Kurulum dosyaları hazır. Uygulama başlatılıyor..." -ForegroundColor Green
    Start-Sleep -Seconds 1
    
    # Launch start_setup.py using venv python with absolute paths
    $PythonPath = Join-Path $TargetDir "venv\Scripts\python.exe"
    $SetupScript = Join-Path $TargetDir "start_setup.py"
    
    # This will handle its own elevation check and hiding console
    Start-Process -FilePath $PythonPath -ArgumentList "`"$SetupScript`"" -WorkingDirectory $TargetDir -WindowStyle Hidden
}
else {
    Write-Host "[HATA] start_setup.py bulunamadı!" -ForegroundColor Red
}


