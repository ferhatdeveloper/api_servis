# EXFIN OPS API - Akıllı Kurulum ve Güncelleme Scripti
# Kullanım: irm bit.ly/opsapi | iex

$ErrorActionPreference = "Stop"
$RepoUrl = "https://github.com/ferhatdeveloper/api_servis.git"
$DefaultDir = "C:\ExfinApi"

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "   EXFIN OPS API - ONE-LINE INSTALLER v5.2" -ForegroundColor Cyan
Write-Host "==========================================`n" -ForegroundColor Cyan

# 1. Yönetici Kontrolü
if (!([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "[HATA] Lütfen PowerShell'i 'Yönetici Olarak' çalıştırın!" -ForegroundColor Red
    return
}

# 2. Çalışma Dizini Belirleme
# 2. Çalışma Dizini Belirleme
$TargetDir = $DefaultDir 
# $TargetDir = Read-Host "Kurulum dizinini girin [Varsayılan: $DefaultDir]"

if (!(Test-Path $TargetDir)) {
    Write-Host "[BİLGİ] Klasör oluşturuluyor: $TargetDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $TargetDir | Out-Null
}

Set-Location $TargetDir

# 3. Git Kontrolü ve İndirme
if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "[UYARI] Git bulunamadı! Lütfen önce Git yükleyin." -ForegroundColor Red
    Start-Process "https://git-scm.com/download/win"
    return
}

if (!(Test-Path ".git")) {
    Write-Host "[BİLGİ] Repo klonlanıyor..." -ForegroundColor Yellow
    git clone $RepoUrl .
}
else {
    Write-Host "[BİLGİ] Mevcut depo güncelleniyor..." -ForegroundColor Yellow
    git fetch origin | Out-Null
    git reset --hard origin/main | Out-Null
}

# 4. Sihirbazı Başlat
if (Test-Path "SETUP.bat") {
    Write-Host "[BAŞARILI] Kurulum dosyaları hazır. Sihirbaz başlatılıyor..." -ForegroundColor Green
    Start-Sleep -Seconds 2
    & ".\SETUP.bat"
}
else {
    Write-Host "[HATA] SETUP.bat bulunamadı! İndirme başarısız olmuş olabilir." -ForegroundColor Red
}
