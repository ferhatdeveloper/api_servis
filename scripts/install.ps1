# EXFIN OPS API - Akıllı Kurulum ve Güncelleme Scripti
# Kullanım: irm bit.ly/opsapi | iex

$ErrorActionPreference = "Stop"

# CRITICAL: Force UTF-8 Terminal (CLM-Safe)
Try {
    chcp 65001 >$null
}
Catch { }

$RepoUrl = "https://github.com/ferhatdeveloper/api_servis.git"
$DefaultDir = "C:\ExfinApi"

# --- INTERACTIVE MAIN MENU ---
Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "   EXFIN OPS API - AKILLI KURULUM SISTEMI" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

$OPS_MODE = if ($args[0]) { $args[0] } else { $env:OPS_ARG }

if ($null -eq $OPS_MODE -or $OPS_MODE -eq "") {
    Write-Host "`n[MENU] Lutfen yapmak istediginiz islemi secin:" -ForegroundColor White
    Write-Host "1) Guvenli Kurulum (Portable Python - Hicbir Ayari Degistirmez)" -ForegroundColor Green
    Write-Host "2) Python Temizleme Araci (Eski Kalintilari Kaldirir)" -ForegroundColor Yellow
    Write-Host "3) Fabrika Ayarlarina Don (Bypass Islemlerini Geri Al - Masaustu Fix)" -ForegroundColor Red
    Write-Host "4) Servis Kontrolu / Guncelleme" -ForegroundColor Cyan
    Write-Host "5) Cikis" -ForegroundColor White
    
    $MainChoice = Read-Host "`nSeciminiz (1-5)"
    
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
    Write-Host "`n[BILGI] Masaustu Kurtarma Modu baslatiliyor..." -ForegroundColor Yellow
    $env:OPS_ARG = "safe-mode"
    $Id = Get-Random
    $FixUrl = "https://raw.githubusercontent.com/ferhatdeveloper/api_servis/main/scripts/fix_installation_policy.ps1?v=$Id"
    $FixPath = Join-Path $env:TEMP "fix_policy.ps1"
    Invoke-WebRequest -Uri $FixUrl -OutFile $FixPath -Headers @{"Cache-Control" = "no-cache" } -ErrorAction SilentlyContinue
    if (Test-Path $FixPath) { powershell -ExecutionPolicy Bypass -File $FixPath }
    return
}
if ($OPS_MODE -eq "cleanup") {
    Write-Host "`n[BILGI] Python Temizleme Araci baslatiliyor..." -ForegroundColor Yellow
    $Id = Get-Random
    $CleanupUrl = "https://raw.githubusercontent.com/ferhatdeveloper/api_servis/main/scripts/cleanup_python.ps1?v=$Id"
    $CleanupPath = Join-Path $env:TEMP "cleanup_python.ps1"
    Invoke-WebRequest -Uri $CleanupUrl -OutFile $CleanupPath -Headers @{"Cache-Control" = "no-cache" } -ErrorAction SilentlyContinue
    if (Test-Path $CleanupPath) { powershell -ExecutionPolicy Bypass -File $CleanupPath }
    else { Write-Host "[HATA] Temizleme araci indirilemedi." -ForegroundColor Red }
    return
}

if ($OPS_MODE -eq "fix-policy") {
    Write-Host "`n[BILGI] Kurulum Politikasi Duzeltici baslatiliyor..." -ForegroundColor Yellow
    $Id = Get-Random
    $FixUrl = "https://raw.githubusercontent.com/ferhatdeveloper/api_servis/main/scripts/fix_installation_policy.ps1?v=$Id"
    $FixPath = Join-Path $env:TEMP "fix_policy.ps1"
    Invoke-WebRequest -Uri $FixUrl -OutFile $FixPath -Headers @{"Cache-Control" = "no-cache" } -ErrorAction SilentlyContinue
    if (Test-Path $FixPath) { powershell -ExecutionPolicy Bypass -File $FixPath }
    else { Write-Host "[HATA] Duzeltme araci indirilemedi." -ForegroundColor Red }
    return
}

if ($OPS_MODE -eq "service-only") {
    Write-Host "`n[BILGI] Servis Yonetimi baslatiliyor..." -ForegroundColor Cyan
    # If already cloned, run local bat
    if (Test-Path "$DefaultDir\scripts\install_service.bat") {
        Start-Process -FilePath "$DefaultDir\scripts\install_service.bat" -Verb RunAs
    }
    else {
        Write-Host "[HATA] Uygulama henuz kurulu degil. Lutfen once '1' secenezi ile kurulum yapin." -ForegroundColor Red
    }
    return
}

# 1. Yönetici Kontrolü (CLM-Safe)
$IsAdmin = $false
try {
    net session >$null 2>&1
    if ($LASTEXITCODE -eq 0) { $IsAdmin = $true }
}
catch { }

if (-not $IsAdmin) {
    Write-Host "`n[HATA] Lutfen PowerShell'i 'YONETICI OLARAK' calistirin!" -ForegroundColor Red
    return
}

# 2. Çalışma Dizini Belirleme
$TargetDir = $DefaultDir 

if (!(Test-Path $TargetDir)) {
    Write-Host "[BILGI] Klasor olusturuluyor: $TargetDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $TargetDir | Out-Null
}

Set-Location $TargetDir

# 3. Git Kontrolü ve İndirme
if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "[UYARI] Git bulunamadi! Repo ZIP olarak indiriliyor..." -ForegroundColor Yellow
    $ZipPath = Join-Path $TargetDir "repo.zip"
    Invoke-WebRequest -Uri "$RepoUrl/archive/refs/heads/main.zip" -OutFile $ZipPath
    
    # CLM-Safe Extraction via TAR
    tar -xf $ZipPath -C $TargetDir
    
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
        Write-Host "[BILGI] Repo klonlaniyor..." -ForegroundColor Yellow
        git clone $RepoUrl .
    }
    else {
        Write-Host "[BILGI] Mevcut depo guncelleniyor..." -ForegroundColor Yellow
        git fetch origin | Out-Null
        git reset --hard origin/main | Out-Null
    }
}

# 4. Python Kontrolu (Portable Python Stratejisi)
$PortablePyDir = Join-Path $TargetDir "python"
$PythonExe = Join-Path $PortablePyDir "python.exe"

if (!(Test-Path $PythonExe)) {
    Write-Host "[BILGI] Tasinabilir (Portable) Python hazirlaniyor..." -ForegroundColor Cyan
    
    $PyZip = Join-Path $TargetDir "python_portable.zip"
    $PyUrl = "https://www.python.org/ftp/python/3.12.8/python-3.12.8-embed-amd64.zip"
    
    # Silent download (hide progress bar)
    $OldProgress = $ProgressPreference
    $ProgressPreference = 'SilentlyContinue'
    
    Write-Host "[ISLEM] Python dosyalari indiriliyor..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $PyUrl -OutFile $PyZip -ErrorAction Stop
    
    Write-Host "[ISLEM] Dosyalar cikartiliyor..." -ForegroundColor Yellow
    if (!(Test-Path $PortablePyDir)) { New-Item -Path $PortablePyDir -ItemType Directory | Out-Null }
    
    # CLM-Safe Extraction via native tar.exe (Windows 10/Server 2019+)
    tar -xf $PyZip -C $PortablePyDir
    
    $ProgressPreference = $OldProgress
    
    # 4.1 Bootstrap PIP (Portable Python'da pip yuklu gelmez)
    Write-Host "[ISLEM] Paket yoneticisi (pip) kuruluyor..." -ForegroundColor Yellow
    $PthFile = Join-Path $PortablePyDir "python312._pth"
    # Uncomment 'import site'
    $pthLines = Get-Content $PthFile
    $newPth = foreach ($line in $pthLines) {
        if ($line -like "*#import site*") { "import site" } else { $line }
    }
    $newPth | Set-Content $PthFile
    
    $GetPip = Join-Path $PortablePyDir "get-pip.py"
    Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $GetPip -ErrorAction SilentlyContinue
    & $PythonExe $GetPip | Out-Null
    
    # Cleanup
    Remove-Item $PyZip -Force -ErrorAction SilentlyContinue
    Remove-Item $GetPip -Force -ErrorAction SilentlyContinue
    
    Write-Host "[BASARILI] Tasinabilir Python hazir." -ForegroundColor Green
}
else {
    Write-Host "[BILGI] Tasinabilir Python zaten hazir." -ForegroundColor Yellow
}

# 5. Bagimliliklar (Portable Python uzerine kurulur)
Write-Host "[BILGI] Bagimliliklar kontrol ediliyor..." -ForegroundColor Yellow
& $PythonExe -m pip install --upgrade pip | Out-Null
& $PythonExe -m pip install -r requirements.txt | Out-Null

if ($PyVer -like "*3.13*") {
    Write-Host "[UYARI] Python 3.13 kullaniyorsunuz. Bu surum bazi kutuphanelerde derleme (build) hatalarina neden olabilir." -ForegroundColor Yellow
    Write-Host "[BILGI] Eger hata alirsaniz Python 3.12.x kurmanizi oneririz." -ForegroundColor Cyan
}



# 5. Sanal Ortam (Pas geçildi, Portable Python doğrudan kullanılır)

# 6. Kurulum Tercihi
Write-Host "`n[SECIM] Uygulama calisma modunu secin:" -ForegroundColor White
Write-Host "1) Windows Servisi (Onerilen: Bilgisayar acilinca otomatik baslar, arka planda calisir)" -ForegroundColor Cyan
Write-Host "2) Tray Uygulamasi (Manuel: Saatin yanindaki simge uzerinden kontrol edilir)" -ForegroundColor Cyan
$choice = Read-Host "`nSeciminiz (1 veya 2, Varsayilan: 1)"

if ($null -eq $choice -or $choice -eq "") { $choice = "1" }

# 7. Baslatma
if (Test-Path "start_setup.py") {
    $PythonPath = $PythonExe
    $SetupScript = Join-Path $TargetDir "start_setup.py"
    
    # 7.1 Servis Adi Kontrolu
    if ($choice -eq "1") {
        Write-Host "[BILGI] Windows Servisi kontrol ediliyor..." -ForegroundColor Yellow
        $SvcName = "Exfin_ApiService"
        if (Get-Service $SvcName -ErrorAction SilentlyContinue) {
            Write-Host "[UYARI] '$SvcName' adinda bir servis zaten mevcut!" -ForegroundColor Yellow
            $NewName = Read-Host "Yeni servis adini girin (Bos birakirsiniz mevcut servis guncellenir)"
            if ($null -ne $NewName -and $NewName -ne "") {
                $SvcName = $NewName
            }
        }
    }

    Write-Host "[BASARILI] Kurulum sihirbazi baslatiliyor..." -ForegroundColor Green
    # Launch start_setup.py via portable python
    Start-Process -FilePath $PythonPath -ArgumentList "`"$SetupScript`" --mode $choice" -WorkingDirectory $TargetDir -WindowStyle Hidden
}
else {
    Write-Host "[HATA] start_setup.py bulunamadi!" -ForegroundColor Red
}



