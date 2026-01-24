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

$RepoUrl = "https://github.com/ferhatdeveloper/api_servis.git"
$DefaultDir = "C:\ExfinApi"

# --- INTERACTIVE MAIN MENU ---
Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "   EXFIN OPS API - AKILLI KURULUM SİSTEMİ" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

$OPS_MODE = if ($args[0]) { $args[0] } else { $env:OPS_ARG }

if ($null -eq $OPS_MODE -or $OPS_MODE -eq "") {
    Write-Host "`n[MENÜ] Lütfen yapmak istediğiniz işlemi seçin:" -ForegroundColor White
    Write-Host "1) Güvenli Kurulum (Portable Python - Hiçbir Ayarı Değiştirmez)" -ForegroundColor Green
    Write-Host "2) Python Temizleme Aracı (Eski Kalıntıları Kaldırır)" -ForegroundColor Yellow
    Write-Host "3) Fabrika Ayarlarına Dön (Bypass İşlemlerini Geri Al - Masaüstü Fix)" -ForegroundColor Red
    Write-Host "4) Servis Kontrolü / Güncelleme" -ForegroundColor Cyan
    Write-Host "5) Çıkış" -ForegroundColor White
    
    $MainChoice = Read-Host "`nSeçiminiz (1-5)"
    
    switch ($MainChoice) {
        "1" { $OPS_MODE = "install" }
        "2" { $OPS_MODE = "cleanup" }
        "3" { $OPS_MODE = "safe-mode" }
        "4" { $OPS_MODE = "service-only" }
        "5" { return }
        default { $OPS_MODE = "install" }
    }
}

# 0. Argument / Menu Action Handling
if ($OPS_MODE -eq "safe-mode") {
    Write-Host "`n[BİLGİ] Masaüstü Kurtarma Modu başlatılıyor..." -ForegroundColor Yellow
    $env:OPS_ARG = "safe-mode"
    $Id = Get-Random
    $FixUrl = "https://raw.githubusercontent.com/ferhatdeveloper/api_servis/main/scripts/fix_installation_policy.ps1?v=$Id"
    $FixPath = Join-Path $env:TEMP "fix_policy.ps1"
    Invoke-WebRequest -Uri $FixUrl -OutFile $FixPath -Headers @{"Cache-Control" = "no-cache" } -ErrorAction SilentlyContinue
    if (Test-Path $FixPath) { & $FixPath }
    return
}
if ($OPS_MODE -eq "cleanup") {
    Write-Host "`n[BİLGİ] Python Temizleme Aracı başlatılıyor..." -ForegroundColor Yellow
    $Id = Get-Random
    $CleanupUrl = "https://raw.githubusercontent.com/ferhatdeveloper/api_servis/main/scripts/cleanup_python.ps1?v=$Id"
    $CleanupPath = Join-Path $env:TEMP "cleanup_python.ps1"
    Invoke-WebRequest -Uri $CleanupUrl -OutFile $CleanupPath -Headers @{"Cache-Control" = "no-cache" } -ErrorAction SilentlyContinue
    if (Test-Path $CleanupPath) { & $CleanupPath }
    else { Write-Host "[HATA] Temizleme aracı indirilemedi." -ForegroundColor Red }
    return
}

if ($OPS_MODE -eq "fix-policy") {
    Write-Host "`n[BİLGİ] Kurulum Politikası Düzeltici başlatılıyor..." -ForegroundColor Yellow
    $Id = Get-Random
    $FixUrl = "https://raw.githubusercontent.com/ferhatdeveloper/api_servis/main/scripts/fix_installation_policy.ps1?v=$Id"
    $FixPath = Join-Path $env:TEMP "fix_policy.ps1"
    Invoke-WebRequest -Uri $FixUrl -OutFile $FixPath -Headers @{"Cache-Control" = "no-cache" } -ErrorAction SilentlyContinue
    if (Test-Path $FixPath) { & $FixPath }
    else { Write-Host "[HATA] Düzeltme aracı indirilemedi." -ForegroundColor Red }
    return
}

if ($OPS_MODE -eq "service-only") {
    Write-Host "`n[BİLGİ] Servis Yönetimi başlatılıyor..." -ForegroundColor Cyan
    # If already cloned, run local bat
    if (Test-Path "$DefaultDir\scripts\install_service.bat") {
        Start-Process -FilePath "$DefaultDir\scripts\install_service.bat" -Verb RunAs
    }
    else {
        Write-Host "[HATA] Uygulama henüz kurulu değil. Lütfen önce '1' seçeneği ile kurulum yapın." -ForegroundColor Red
    }
    return
}

# 1. Yönetici Kontrolü
if (!([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "`n[HATA] Lütfen PowerShell'i 'YÖNETİCİ OLARAK' çalıştırın!" -ForegroundColor Red
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

# 4. Python Kontrolü (Portable Python Stratejisi)
$PortablePyDir = Join-Path $TargetDir "python"
$PythonExe = Join-Path $PortablePyDir "python.exe"

if (!(Test-Path $PythonExe)) {
    Write-Host "[BİLGİ] Taşınabilir (Portable) Python hazırlanıyor... (Hiçbir sistem ayarı değiştirilmez)" -ForegroundColor Cyan
    
    $PyZip = Join-Path $env:TEMP "python_portable.zip"
    $PyUrl = "https://www.python.org/ftp/python/3.12.8/python-3.12.8-embed-amd64.zip"
    
    Write-Host "[İŞLEM] Python dosyaları indiriliyor..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $PyUrl -OutFile $PyZip
    
    Write-Host "[İŞLEM] Dosyalar çıkartılıyor..." -ForegroundColor Yellow
    if (!(Test-Path $PortablePyDir)) { New-Item -Path $PortablePyDir -ItemType Directory }
    Expand-Archive -Path $PyZip -DestinationPath $PortablePyDir -Force
    
    # 4.1 Bootstrap PIP (Portable Python'da pip yüklü gelmez)
    Write-Host "[İŞLEM] Paket yöneticisi (pip) kuruluyor..." -ForegroundColor Yellow
    $PthFile = Join-Path $PortablePyDir "python312._pth"
    # Uncomment 'import site' in .pth file to allow site-packages
    (Get-Content $PthFile) -replace "#import site", "import site" | Set-Content $PthFile
    
    $GetPip = Join-Path $PortablePyDir "get-pip.py"
    Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $GetPip
    & $PythonExe $GetPip | Out-Null
    
    Remove-Item $PyZip -Force
    Write-Host "[BAŞARILI] Taşınabilir Python hazır." -ForegroundColor Green
}
else {
    Write-Host "[BİLGİ] Taşınabilir Python zaten hazır." -ForegroundColor Yellow
}

# 5. Bağımlılıklar (Portable Python üzerine kurulur)
Write-Host "[BİLGİ] Bağımlılıklar kontrol ediliyor..." -ForegroundColor Yellow
& $PythonExe -m pip install --upgrade pip | Out-Null
& $PythonExe -m pip install -r requirements.txt | Out-Null

if ($PyVer -like "*3.13*") {
    Write-Host "[UYARI] Python 3.13 kullanıyorsunuz. Bu sürüm bazı kütüphanelerde derleme (build) hatalarına neden olabilir." -ForegroundColor Yellow
    Write-Host "[BİLGİ] Eğer hata alırsanız Python 3.12.x kurmanızı öneririz." -ForegroundColor Cyan
}



# 5. Sanal Ortam (Pas geçildi, Portable Python doğrudan kullanılır)

# 6. Kurulum Tercihi
Write-Host "`n[SEÇİM] Uygulama çalışma modunu seçin:" -ForegroundColor White
Write-Host "1) Windows Servisi (Önerilen: Bilgisayar açılınca otomatik başlar, arka planda çalışır)" -ForegroundColor Cyan
Write-Host "2) Tray Uygulaması (Manuel: Saatin yanındaki simge üzerinden kontrol edilir)" -ForegroundColor Cyan
$choice = Read-Host "`nSeçiminiz (1 veya 2, Varsayılan: 1)"

if ($null -eq $choice -or $choice -eq "") { $choice = "1" }

# 7. Başlatma
if (Test-Path "start_setup.py") {
    $PythonPath = $PythonExe
    $SetupScript = Join-Path $TargetDir "start_setup.py"
    
    # 7.1 Servis Adı Kontrolü
    if ($choice -eq "1") {
        Write-Host "[BİLGİ] Windows Servisi kontrol ediliyor..." -ForegroundColor Yellow
        $SvcName = "Exfin_ApiService"
        if (Get-Service $SvcName -ErrorAction SilentlyContinue) {
            Write-Host "[UYARI] '$SvcName' adında bir servis zaten mevcut!" -ForegroundColor Yellow
            $NewName = Read-Host "Yeni servis adını girin (Boş bırakırsanız mevcut servis güncellenir)"
            if ($null -ne $NewName -and $NewName -ne "") {
                $SvcName = $NewName
            }
        }
    }

    Write-Host "[BAŞARILI] Kurulum sihirbazı başlatılıyor..." -ForegroundColor Green
    # Launch start_setup.py via portable python
    Start-Process -FilePath $PythonPath -ArgumentList "`"$SetupScript`" --mode $choice" -WorkingDirectory $TargetDir -WindowStyle Hidden
}
else {
    Write-Host "[HATA] start_setup.py bulunamadı!" -ForegroundColor Red
}



