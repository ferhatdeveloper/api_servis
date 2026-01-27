# EXFIN OPS API - Akıllı Kurulum ve Güncelleme Scripti
# Kullanım: [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointType]::Tls12; irm bit.ly/opsapi | iex

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ErrorActionPreference = "Stop"

# VERSION: 1.1.3 (URL & IE Fix)

# Write-Safe: Server 2012 uyumlulugu icin [Console]::WriteLine kullanir
function Write-Safe($msg, $color = "White") {
    try {
        # Server 2012'de Write-Host 0x1F hatasina neden olabildigi icin low-level [Console] tercih edildi.
        [Console]::ResetColor()
        switch ($color) {
            "Cyan" { [Console]::ForegroundColor = [ConsoleColor]::Cyan }
            "Green" { [Console]::ForegroundColor = [ConsoleColor]::Green }
            "Yellow" { [Console]::ForegroundColor = [ConsoleColor]::Yellow }
            "Red" { [Console]::ForegroundColor = [ConsoleColor]::Red }
            "White" { [Console]::ForegroundColor = [ConsoleColor]::White }
            "Gray" { [Console]::ForegroundColor = [ConsoleColor]::Gray } # Added for consistency, though not in original snippet
            default { [Console]::ForegroundColor = [ConsoleColor]::White }
        }
        [Console]::WriteLine($msg)
        [Console]::ResetColor()
    }
    catch {
        Write-Output $msg
    }
}

# GitHub URL'sinde .git eki ZIP indirmeyi bozabilir, temiz halini kullanalim.
$RepoUrl = "https://github.com/ferhatdeveloper/api_servis"
$DefaultDir = "C:\ExfinApi"

# --- INTERACTIVE MAIN MENU ---
Write-Safe "`n==========================================" "Cyan"
Write-Safe "   EXFIN OPS API - SMART INSTALLER (v1.1.3)" "Cyan"
Write-Safe "==========================================" "Cyan"

$OPS_MODE = if ($args[0]) { $args[0] } else { $env:OPS_ARG }

if ($null -eq $OPS_MODE -or $OPS_MODE -eq "") {
    Write-Safe "`n[MENU] Lutfen yapmak istediginiz islemi secin:" "White"
    Write-Safe "1) Standart Kurulum (Yerel Python 3.12 - Onerilen)" "Green"
    Write-Safe "2) Sistem Python ile Kurulum (Varsa kullanilir)" "Cyan"
    Write-Safe "3) Python Temizleme Araci (Eski Kalintilari Kaldirir)" "Yellow"
    Write-Safe "4) Fabrika Ayarlarina Don (Masaustu Fix)" "Red"
    Write-Safe "5) Servis Kontrolu / Guncelleme" "Cyan"
    Write-Safe "6) API Guncelle (Son Degisiklikleri Cek ve Uygula)" "Green"
    Write-Safe "7) Cikis" "White"
    
    # Read-Host'u Write-Output ile destekleyelim (0x1F riski)
    [Console]::Write("`nSeciminiz (1-7): ")
    $MainChoice = [Console]::ReadLine()
    
    switch ($MainChoice) {
        "1" { $OPS_MODE = "portable" }
        "2" { $OPS_MODE = "system-python" }
        "3" { $OPS_MODE = "cleanup" }
        "4" { $OPS_MODE = "safe-mode" }
        "5" { $OPS_MODE = "service-only" }
        "6" { $OPS_MODE = "update-only" }
        "7" { return }
        default { $OPS_MODE = "portable" }
    }
}

# 0. Argument / Menu Action Handling
if ($OPS_MODE -eq "safe-mode") {
    Write-Safe "`n[BILGI] Masaustu Kurtarma Modu baslatiliyor..." "Yellow"
    $env:OPS_ARG = "safe-mode"
    $Id = Get-Random
    $FixUrl = "https://raw.githubusercontent.com/ferhatdeveloper/api_servis/main/scripts/fix_installation_policy.ps1?v=$Id"
    $FixPath = Join-Path $env:TEMP "fix_policy.ps1"
    Invoke-WebRequest -Uri $FixUrl -OutFile $FixPath -Headers @{"Cache-Control" = "no-cache" } -UseBasicParsing -ErrorAction SilentlyContinue
    if (Test-Path $FixPath) { powershell -ExecutionPolicy Bypass -File $FixPath }
    return
}
if ($OPS_MODE -eq "cleanup") {
    Write-Safe "`n[BILGI] Python Temizleme Araci baslatiliyor..." "Yellow"
    $Id = Get-Random
    $CleanupUrl = "https://raw.githubusercontent.com/ferhatdeveloper/api_servis/main/scripts/cleanup_python.ps1?v=$Id"
    $CleanupPath = Join-Path $env:TEMP "cleanup_python.ps1"
    Invoke-WebRequest -Uri $CleanupUrl -OutFile $CleanupPath -Headers @{"Cache-Control" = "no-cache" } -UseBasicParsing -ErrorAction SilentlyContinue
    if (Test-Path $CleanupPath) { powershell -ExecutionPolicy Bypass -File $CleanupPath }
    else { Write-Safe "[HATA] Temizleme araci indirilemedi." "Red" }
    return
}

if ($OPS_MODE -eq "fix-policy") {
    Write-Safe "`n[BILGI] Kurulum Politikasi Duzeltici baslatiliyor..." "Yellow"
    $Id = Get-Random
    $FixUrl = "https://raw.githubusercontent.com/ferhatdeveloper/api_servis/main/scripts/fix_installation_policy.ps1?v=$Id"
    $FixPath = Join-Path $env:TEMP "fix_policy.ps1"
    Invoke-WebRequest -Uri $FixUrl -OutFile $FixPath -Headers @{"Cache-Control" = "no-cache" } -UseBasicParsing -ErrorAction SilentlyContinue
    if (Test-Path $FixPath) { powershell -ExecutionPolicy Bypass -File $FixPath }
    else { Write-Safe "[HATA] Duzeltme araci indirilemedi." "Red" }
    return
}

if ($OPS_MODE -eq "service-only") {
    Write-Safe "`n[BILGI] Servis Yonetimi baslatiliyor..." "Cyan"
    # If already cloned, run local bat
    if (Test-Path "$DefaultDir\scripts\install_service.bat") {
        Start-Process -FilePath "$DefaultDir\scripts\install_service.bat" -Verb RunAs
    }
    else {
        Write-Safe "[HATA] Uygulama henuz kurulu degil. Lutfen once '1' secenezi ile kurulum yapin." "Red"
    }
    return
}

if ($OPS_MODE -eq "update-only") {
    Write-Safe "`n[BILGI] API Guncelleme Modu baslatiliyor..." "Cyan"
    
    # 1. Update Repo
    if (Test-Path "$DefaultDir\.git") {
        Set-Location $DefaultDir
        Write-Safe "> Git guncellemesi yapiliyor..." "Yellow"
        git count-objects -v >$null 2>&1 
        if ($LASTEXITCODE -eq 0) {
            git fetch origin
            git reset --hard origin/main
            Write-Safe "  > Git guncellendi." "Green"
        }
        else {
            Write-Safe "  > Git hatasi veya repo bozuk. Yine de devam ediliyor..." "Red"
        }
    }
    else {
        Write-Safe "  > Git Reposu bulunamadi ($DefaultDir). Guncelleme atlatiliyor." "Yellow"
    }

    # 2. Update Service
    Write-Safe "> Servis yeniden baslatiliyor..." "Yellow"
    if (Get-Service "Exfin_ApiService" -ErrorAction SilentlyContinue) {
        Restart-Service "Exfin_ApiService" -Force
        Write-Safe "  > Servis guncellendi ve yeniden baslatildi." "Green"
    }
    else {
        Write-Safe "  > Servis kurulu degil." "Gray"
    }
    
    Write-Safe "`n[BASARILI] Guncelleme islemi tamamlandi." "Green"
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
    Write-Safe "`n[HATA] Lutfen PowerShell'i 'YONETICI OLARAK' calistirin!" "Red"
    return
}

# 2. Çalışma Dizini Belirleme
$TargetDir = $DefaultDir 

if (!(Test-Path $TargetDir)) {
    Write-Safe "[BILGI] Klasor olusturuluyor: $TargetDir" "Yellow"
    New-Item -ItemType Directory -Path $TargetDir | Out-Null
}

Set-Location $TargetDir

# 3. Git Kontrolü ve İndirme
if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Safe "[UYARI] Git bulunamadi! Repo ZIP olarak indiriliyor..." "Yellow"
    $ZipPath = Join-Path $TargetDir "repo.zip"
    $ZipUrl = "$RepoUrl/archive/refs/heads/main.zip"
    
    try {
        Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipPath -UseBasicParsing -ErrorAction Stop
    }
    catch {
        # Fallback to direct archive URL if refs/heads fails
        $ZipUrl = "$RepoUrl/archive/main.zip"
        Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipPath -UseBasicParsing -ErrorAction Stop
    }
    
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
        Write-Safe "[BILGI] Repo klonlaniyor..." "Yellow"
        git clone "$RepoUrl.git" .
    }
    else {
        Write-Safe "[BILGI] Mevcut depo guncelleniyor..." "Yellow"
        git fetch origin | Out-Null
        git reset --hard origin/main | Out-Null
    }
}

# 4. Python Ortami Hazirlama
$PythonExe = ""
$VenvDir = Join-Path $TargetDir "venv"
$PortablePyDir = Join-Path $TargetDir "python"

if ($OPS_MODE -eq "system-python") {
    Write-Safe "[BILGI] Sistem Python modu secildi. Sistem Python kontrol ediliyor..." "Cyan"
    $SystemPy = Get-Command python.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
    
    if ($SystemPy) {
        Write-Safe "[OK] Sistem Python bulundu: $SystemPy" "Green"
        if (!(Test-Path $VenvDir)) {
            Write-Safe "[ISLEM] Sanal ortam (venv) olusturuluyor..." "Yellow"
            & python -m venv $VenvDir
        }
        $PythonExe = Join-Path $VenvDir "Scripts\python.exe"
    }
    else {
        Write-Safe "[UYARI] Sistemde Python bulunamadi! Otomatik olarak 'Yerel' moda geciliyor." "Yellow"
        $OPS_MODE = "portable"
    }
}

if ($OPS_MODE -eq "portable") {
    Write-Safe "[BILGI] Tasinabilir (Portable) Python hazirlaniyor..." "Cyan"
    $PythonExe = Join-Path $PortablePyDir "python.exe"
    
    if (!(Test-Path $PythonExe)) {
        $PyZip = Join-Path $TargetDir "python_portable.zip"
        $PyUrl = "https://www.python.org/ftp/python/3.12.8/python-3.12.8-embed-amd64.zip"
        
        $OldProgress = $ProgressPreference
        $ProgressPreference = 'SilentlyContinue'
        
        Write-Safe "[ISLEM] Python dosyalari indiriliyor..." "Yellow"
        Invoke-WebRequest -Uri $PyUrl -OutFile $PyZip -UseBasicParsing -ErrorAction Stop
        
        Write-Safe "[ISLEM] Dosyalar cikartiliyor..." "Yellow"
        if (!(Test-Path $PortablePyDir)) { New-Item -Path $PortablePyDir -ItemType Directory | Out-Null }
        tar -xf $PyZip -C $PortablePyDir
        
        $ProgressPreference = $OldProgress
        
        Write-Safe "[ISLEM] Paket yoneticisi (pip) kuruluyor..." "Yellow"
        $PthFile = Join-Path $PortablePyDir "python312._pth"
        $pthLines = Get-Content $PthFile
        $newPth = foreach ($line in $pthLines) {
            if ($line -like "*#import site*") { "import site" } else { $line }
        }
        $newPth | Set-Content $PthFile
        
        $GetPip = Join-Path $PortablePyDir "get-pip.py"
        Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $GetPip -UseBasicParsing -ErrorAction SilentlyContinue
        & $PythonExe $GetPip | Out-Null
        
        Remove-Item $PyZip -Force -ErrorAction SilentlyContinue
        Remove-Item $GetPip -Force -ErrorAction SilentlyContinue
        Write-Safe "[BASARILI] Tasinabilir Python hazir." "Green"
    }
    else {
        Write-Safe "[BILGI] Tasinabilir Python zaten hazir." "Yellow"
    }
}

# 5. Bagimliliklar (Portable Python uzerine kurulur)
Write-Safe "[BILGI] Bagimliliklar kontrol ediliyor... (1-2 dakika surebilir)" "Yellow"
& $PythonExe -m pip install --upgrade pip
& $PythonExe -m pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Safe "[HATA] Bagimliliklar kurulurken bir hata olustu!" "Red"
    pause
    return
}

if ($PyVer -like "*3.13*") {
    Write-Safe "[UYARI] Python 3.13 kullaniyorsunuz. Bu surum bazi kutuphanelerde derleme (build) hatalarina neden olabilir." "Yellow"
    Write-Safe "[BILGI] Eger hata alirsaniz Python 3.12.x kurmanizi oneririz." "Cyan"
}



# 5. Sanal Ortam (Pas gecildi, Portable Python dogrudan kullanilir)

# 6. Kurulum Tercihi
Write-Safe "`n[SECIM] Uygulama calisma modunu secin:" "White"
Write-Safe "1) Windows Servisi (Onerilen)" "Cyan"
Write-Safe "2) Tray Uygulamasi (Manuel)" "Cyan"
$choice = Read-Host "`nSeciminiz (1 veya 2, Varsayilan: 1)"

if ($null -eq $choice -or $choice -eq "") { $choice = "1" }

# 7. Baslatma
if (Test-Path "$TargetDir\start_setup.py") {
    $PythonPath = $PythonExe
    $SetupScript = "$TargetDir\start_setup.py"
    
    # 7.1 Servis Adi Kontrolu
    if ($choice -eq "1") {
        Write-Safe "[BILGI] Windows Servisi kontrol ediliyor..." "Yellow"
        $SvcName = "Exfin_ApiService"
        if (Get-Service $SvcName -ErrorAction SilentlyContinue) {
            Write-Safe "[UYARI] '$SvcName' adinda bir servis zaten mevcut!" "Yellow"
            $NewName = Read-Host "Yeni servis adini girin (Bos birakirsiniz mevcut servis guncellenir)"
            if ($null -ne $NewName -and $NewName -ne "") {
                $SvcName = $NewName
            }
        }
    }

    Write-Safe "[BASARILI] Kurulum sihirbazi baslatiliyor..." "Green"
    # Launch start_setup.py via portable python
    Start-Process -FilePath $PythonPath -ArgumentList "`"$SetupScript`" --mode $choice" -WorkingDirectory $TargetDir -WindowStyle Hidden
}
else {
    Write-Safe "[HATA] start_setup.py bulunamadi!" "Red"
    pause
}
