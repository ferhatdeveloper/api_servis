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
    Write-Host "1) Standart Kurulum (Sistem Python + Venv - Onerilen)" -ForegroundColor Green
    Write-Host "2) Guvenli Kurulum (Portable Python - Hiçbir Ayarı Değiştirmez)" -ForegroundColor Cyan
    Write-Host "3) Python Temizleme Aracı (Eski Kalıntıları Kaldırır)" -ForegroundColor Yellow
    Write-Host "4) Fabrika Ayarlarina Don (Bypass Islemlerini Geri Al - Masaustu Fix)" -ForegroundColor Red
    Write-Host "5) Servis Kontrolu / Guncelleme" -ForegroundColor Cyan
    Write-Host "6) API Guncelle (Son Degisiklikleri Cek ve Uygula)" -ForegroundColor Green
    Write-Host "7) Cikis" -ForegroundColor White
    
    $MainChoice = Read-Host "`nSeciminiz (1-7)"
    
    switch ($MainChoice) {
        "1" { $OPS_MODE = "standard" }
        "2" { $OPS_MODE = "portable" }
        "3" { $OPS_MODE = "cleanup" }
        "4" { $OPS_MODE = "safe-mode" }
        "5" { $OPS_MODE = "service-only" }
        "6" { $OPS_MODE = "update-only" }
        "7" { return }
        default { $OPS_MODE = "standard" }
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

if ($OPS_MODE -eq "update-only") {
    Write-Host "`n[BILGI] API Guncelleme Modu baslatiliyor..." -ForegroundColor Cyan
    
    # 1. Update Repo
    if (Test-Path "$DefaultDir\.git") {
        Set-Location $DefaultDir
        Write-Host "> Git guncellemesi yapiliyor..." -ForegroundColor Yellow
        git count-objects -v >$null 2>&1 
        if ($LASTEXITCODE -eq 0) {
            git fetch origin
            git reset --hard origin/main
            Write-Host "  > Git guncellendi." -ForegroundColor Green
        }
        else {
            Write-Host "  > Git hatasi veya repo bozuk. Yine de devam ediliyor..." -ForegroundColor Red
        }
    }
    else {
        Write-Host "  > Git Reposu bulunamadi ($DefaultDir). Guncelleme atlatiliyor." -ForegroundColor Yellow
    }

    # 2. Update Service
    Write-Host "> Servis yeniden baslatiliyor..." -ForegroundColor Yellow
    if (Get-Service "Exfin_ApiService" -ErrorAction SilentlyContinue) {
        Restart-Service "Exfin_ApiService" -Force
        Write-Host "  > Servis guncellendi ve yeniden baslatildi." -ForegroundColor Green
    }
    else {
        Write-Host "  > Servis kurulu degil." -ForegroundColor Gray
    }
    
    Write-Host "`n[BASARILI] Guncelleme islemi tamamlandi." -ForegroundColor Green
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

# 4. Python Ortami Hazirlama
$PythonExe = ""
$VenvDir = Join-Path $TargetDir "venv"
$PortablePyDir = Join-Path $TargetDir "python"

if ($OPS_MODE -eq "standard") {
    Write-Host "[BILGI] Standart Kurulum secildi. Sistem Python kontrol ediliyor..." -ForegroundColor Cyan
    $SystemPy = Get-Command python.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
    
    if ($SystemPy) {
        Write-Host "[OK] Sistem Python bulundu: $SystemPy" -ForegroundColor Green
        if (!(Test-Path $VenvDir)) {
            Write-Host "[ISLEM] Sanal ortam (venv) olusturuluyor..." -ForegroundColor Yellow
            & python -m venv $VenvDir
        }
        $PythonExe = Join-Path $VenvDir "Scripts\python.exe"
    }
    else {
        Write-Host "[UYARI] Sistemde Python bulunamadi! Otomatik olarak 'Tasinabilir' moda geciliyor." -ForegroundColor Yellow
        $OPS_MODE = "portable"
    }
}

if ($OPS_MODE -eq "portable") {
    Write-Host "[BILGI] Tasinabilir (Portable) Python hazirlaniyor..." -ForegroundColor Cyan
    $PythonExe = Join-Path $PortablePyDir "python.exe"
    
    if (!(Test-Path $PythonExe)) {
        $PyZip = Join-Path $TargetDir "python_portable.zip"
        $PyUrl = "https://www.python.org/ftp/python/3.12.8/python-3.12.8-embed-amd64.zip"
        
        $OldProgress = $ProgressPreference
        $ProgressPreference = 'SilentlyContinue'
        
        Write-Host "[ISLEM] Python dosyalari indiriliyor..." -ForegroundColor Yellow
        Invoke-WebRequest -Uri $PyUrl -OutFile $PyZip -ErrorAction Stop
        
        Write-Host "[ISLEM] Dosyalar cikartiliyor..." -ForegroundColor Yellow
        if (!(Test-Path $PortablePyDir)) { New-Item -Path $PortablePyDir -ItemType Directory | Out-Null }
        tar -xf $PyZip -C $PortablePyDir
        
        $ProgressPreference = $OldProgress
        
        Write-Host "[ISLEM] Paket yoneticisi (pip) kuruluyor..." -ForegroundColor Yellow
        $PthFile = Join-Path $PortablePyDir "python312._pth"
        $pthLines = Get-Content $PthFile
        $newPth = foreach ($line in $pthLines) {
            if ($line -like "*#import site*") { "import site" } else { $line }
        }
        $newPth | Set-Content $PthFile
        
        $GetPip = Join-Path $PortablePyDir "get-pip.py"
        Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $GetPip -ErrorAction SilentlyContinue
        & $PythonExe $GetPip | Out-Null
        
        Remove-Item $PyZip -Force -ErrorAction SilentlyContinue
        Remove-Item $GetPip -Force -ErrorAction SilentlyContinue
        Write-Host "[BASARILI] Tasinabilir Python hazir." -ForegroundColor Green
    }
    else {
        Write-Host "[BILGI] Tasinabilir Python zaten hazir." -ForegroundColor Yellow
    }
}

# 5. Bagimliliklar (Portable Python uzerine kurulur)
Write-Host "[BILGI] Bagimliliklar kontrol ediliyor... (Bu islem 1-2 dakika surebilir)" -ForegroundColor Yellow
& $PythonExe -m pip install --upgrade pip
& $PythonExe -m pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "[HATA] Bagimliliklar kurulurken bir hata olustu!" -ForegroundColor Red
    pause
    return
}

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
if (Test-Path "$TargetDir\start_setup.py") {
    $PythonPath = $PythonExe
    $SetupScript = "$TargetDir\start_setup.py"
    
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
    Write-Host "[HATA] start_setup.py bulunamadi! (Yol: $TargetDir\start_setup.py)" -ForegroundColor Red
    pause
}
