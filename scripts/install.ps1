# EXFIN OPS API - Akıllı Kurulum ve Güncelleme Scripti
# Kullanım: [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointType]::Tls12; irm bit.ly/opsapi | iex

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# VERSION: 1.1.13 (Standardized Fix)

# OS Version Check
$OSVersion = [Environment]::OSVersion.Version
$IsLegacyOS = $OSVersion.Major -lt 6 -or ($OSVersion.Major -eq 6 -and $OSVersion.Minor -lt 3)

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

# Expand-Zip: tar olmayan eski sistemler icin ZIP acma fonksiyonu (Senkronize)
function Expand-Zip($ZipPath, $DestDir) {
    Write-Safe "[ISLEM] Dosyalar cikartiliyor (Lutfen bekleyin...)" "Yellow"
    if (!(Test-Path $DestDir)) { New-Item -ItemType Directory -Path $DestDir | Out-Null }
    
    try {
        if (Get-Command Expand-Archive -ErrorAction SilentlyContinue) {
            Write-Safe "> Method: Expand-Archive" "Gray"
            Expand-Archive -Path $ZipPath -DestinationPath $DestDir -Force
        }
        else {
            Write-Safe "> Method: .NET ZipFile" "Gray"
            Add-Type -AssemblyName System.IO.Compression.FileSystem
            [System.IO.Compression.ZipFile]::ExtractToDirectory($ZipPath, $DestDir)
        }
    }
    catch {
        # En eski sistemler icin COM objesi fallback (Senkronizasyon eklenmis hali)
        Write-Safe "> Method: COM Shell (Legacy)" "Gray"
        $shell = New-Object -ComObject Shell.Application
        $zipFile = $shell.NameSpace($ZipPath)
        $destination = $shell.NameSpace($DestDir)
        
        $itemCountBefore = $destination.Items().Count
        $zipItemCount = $zipFile.Items().Count
        
        $destination.CopyHere($zipFile.Items(), 16) # 16: Yes to All
        
        # Senkronizasyon Beklemesi: Dosya sayisi esitlenene kadar bekle (max 30 sn)
        $waitCount = 0
        while (($destination.Items().Count -lt ($itemCountBefore + $zipItemCount)) -and ($waitCount -lt 60)) {
            Start-Sleep -Milliseconds 500
            $waitCount++
        }
    }
    
    # Kisa bir bekleme (Sistemin dosyalari serbest birakmasi icin)
    Start-Sleep -Seconds 1
}

# GitHub URL'sinde .git eki ZIP indirmeyi bozabilir, temiz halini kullanalim.
$RepoUrl = "https://github.com/ferhatdeveloper/api_servis"
$DefaultDir = "C:\ExfinApi"

# --- INTERACTIVE MAIN MENU ---
Write-Safe "`n==========================================" "Cyan"
Write-Safe "   EXFIN OPS API - SMART INSTALLER (v1.1.13)" "Cyan"
Write-Safe "==========================================" "Cyan"

$OPS_MODE = if ($args[0]) { $args[0] } else { $env:OPS_ARG }

if ($null -eq $OPS_MODE -or $OPS_MODE -eq "") {
    Write-Safe "`n[MENU] Lutfen yapmak istediginiz islemi secin:" "White"
    Write-Safe "1) Standart Kurulum (Onerilen)" "Green"
    Write-Safe "2) Sistem Python ile Kurulum" "Cyan"
    Write-Safe "3) Python Temizleme Araci (Eski Kalintilari Kaldirir)" "Yellow"
    Write-Safe "4) Fabrika Ayarlarina Don" "Red"
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

if ($IsLegacyOS) {
    Write-Safe "[BILGI] Ultra-Legacy isletim sistemi algilandi (v$($OSVersion.Major).$($OSVersion.Minor))." "Yellow"
    Write-Safe "        Uyumluluk icin Python 3.8.10 kullanilacak." "Yellow"
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
    
    # tar yerine Expand-Zip kullaniliyor
    Expand-Zip -ZipPath $ZipPath -DestDir $TargetDir
    
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
    
    # Onceki cokmus processleri temizleyelim (Hata vermemesi icin korumali)
    Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

    # Eger yanlis surum (3.9+) varsa ve sistem 2012 ise temizle
    if (Test-Path $PythonExe) {
        $VerInfo = try { & $PythonExe --version 2>&1 } catch { "Crash" }
        if ($IsLegacyOS -and ($VerInfo -like "*3.12*" -or $VerInfo -like "*3.10*" -or $VerInfo -eq "Crash")) {
            Write-Safe "[UYARI] Uyumsuz Python surumu tespit edildi. 3.8.10 ile degistiriliyor..." "Yellow"
            Remove-Item $PortablePyDir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }

    if (!(Test-Path $PythonExe)) {
        $PyZip = Join-Path $TargetDir "python_portable.zip"
        
        if ($IsLegacyOS) {
            # Server 2012 (6.2) icin son kararli surum 3.8.10'dur.
            $PyUrl = "https://www.python.org/ftp/python/3.8.10/python-3.8.10-embed-amd64.zip"
            $PyVerShort = "38"
        }
        else {
            $PyUrl = "https://www.python.org/ftp/python/3.12.8/python-3.12.8-embed-amd64.zip"
            $PyVerShort = "312"
        }
        
        $OldProgress = $ProgressPreference
        $ProgressPreference = 'SilentlyContinue'
        
        Write-Safe "[ISLEM] Python dosyalari indiriliyor..." "Yellow"
        Invoke-WebRequest -Uri $PyUrl -OutFile $PyZip -UseBasicParsing -ErrorAction Stop
        
        Expand-Zip -ZipPath $PyZip -DestDir $PortablePyDir
        
        $ProgressPreference = $OldProgress
        
        if (!(Test-Path $PythonExe)) {
            Write-Safe "[HATA] Python dosyalari cikartilamadi! ($PythonExe bulunamadi)" "Red"
            pause
            return
        }
        
        Write-Safe "[ISLEM] Paket yoneticisi (pip) kuruluyor..." "Yellow"
        # .pth dosyasi surume gore python38._pth veya python312._pth olur
        $PthFile = Join-Path $PortablePyDir "python$($PyVerShort)._pth"
        if (Test-Path $PthFile) {
            $pthLines = Get-Content $PthFile
            $newPth = foreach ($line in $pthLines) {
                if ($line -like "*#import site*") { "import site" } else { $line }
            }
            $newPth | Set-Content $PthFile
        }
        
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

# 5.1 VC++ Redistributable Kontrolu ve Otomatik Kurulum
Write-Safe "[ISLEM] Visual C++ Redistributable (2015-2022) kontrol ediliyor..." "Yellow"
$VCRedistInstalled = $false
try {
    # 2015-2022 (v14) kontrolü
    if (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" -ErrorAction SilentlyContinue) { $VCRedistInstalled = $true }
    if (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\VC\Runtime\Bindable\x64" -ErrorAction SilentlyContinue) { $VCRedistInstalled = $true }
}
catch { }

if (-not $VCRedistInstalled) {
    Write-Safe "[UYARI] Visual C++ Redistributable eksik! Otomatik kuruluyor..." "Red"
    $VcRedistPath = Join-Path $env:TEMP "vc_redist.x64.exe"
    $VcUrl = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
    
    try {
        Write-Safe "[ISLEM] Kurulum dosyasi indiriliyor..." "Yellow"
        Invoke-WebRequest -Uri $VcUrl -OutFile $VcRedistPath -UseBasicParsing -ErrorAction Stop
        
        Write-Safe "[ISLEM] Sessiz kurulum baslatildi (Lutfen bekleyin...)" "Yellow"
        $Process = Start-Process -FilePath $VcRedistPath -ArgumentList "/install", "/quiet", "/norestart" -PassThru -Wait
        
        if ($Process.ExitCode -eq 0 -or $Process.ExitCode -eq 3010) {
            Write-Safe "[BASARILI] Visual C++ Redistributable kuruldu." "Green"
            if ($Process.ExitCode -eq 3010) { Write-Safe "[NOT] Sistemin yeniden baslatilmasi gerekebilir." "Gray" }
        }
        else {
            Write-Safe "[HATA] VC++ kurulumu hata koduyla bitti: $($Process.ExitCode)" "Red"
        }
        Remove-Item $VcRedistPath -Force -ErrorAction SilentlyContinue
    }
    catch {
        Write-Safe "[HATA] VC++ indirilemedi veya kurulamadi. Lutfen manuel kurun: $VcUrl" "Red"
    }
}
else {
    Write-Safe "[OK] Visual C++ Redistributable zaten yuklu." "Green"
}

# 5.1.a Node.js Kontrolu ve Otomatik Kurulum
Write-Safe "[ISLEM] Node.js kontrol ediliyor..." "Yellow"

$NodeCmd = Get-Command node -ErrorAction SilentlyContinue
$NeedsNodeInstall = $false

if (!$NodeCmd) {
    $NeedsNodeInstall = $true
}
else {
    $CurrentVer = & node -v
    Write-Safe "[BILGI] Mevcut Node.js surumu: $CurrentVer" "Cyan"
    # Versiyon kontrolu (v20.17.0 alti ise guncelle)
    if ($CurrentVer -match "v(\d+)\.(\d+)") {
        $Major = [int]$Matches[1]
        $Minor = [int]$Matches[2]
        if ($Major -lt 20 -or ($Major -eq 20 -and $Minor -lt 17)) {
            Write-Safe "[UYARI] Node.js surumu cok eski! Guncelleme gerekiyor." "Yellow"
            $NeedsNodeInstall = $true
        }
    }
}

if ($NeedsNodeInstall) {
    Write-Safe "[ISLEM] Node.js v22 LTS kuruluyor/guncelleniyor..." "Yellow"
    $NodeInstallerPath = Join-Path $env:TEMP "node_installer.msi"
    $NodeUrl = "https://nodejs.org/dist/v22.13.1/node-v22.13.1-x64.msi"
    
    try {
        Write-Safe "[ISLEM] Node.js yukleyici indiriliyor..." "Yellow"
        Invoke-WebRequest -Uri $NodeUrl -OutFile $NodeInstallerPath -UseBasicParsing -ErrorAction Stop
        
        Write-Safe "[ISLEM] Node.js sessiz kurulum baslatildi (Lutfen bekleyin...)" "Yellow"
        $Process = Start-Process -FilePath "msiexec.exe" -ArgumentList "/i", "`"$NodeInstallerPath`"", "/quiet", "/norestart" -PassThru -Wait
        
        if ($Process.ExitCode -eq 0) {
            Write-Safe "[BASARILI] Node.js guncellendi. ✅" "Green"
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        }
        else {
            Write-Safe "[HATA] Node.js kurulumu hata koduyla bitti: $($Process.ExitCode)" "Red"
        }
        Remove-Item $NodeInstallerPath -Force -ErrorAction SilentlyContinue
    }
    catch {
        Write-Safe "[HATA] Node.js indirilemedi veya kurulamadi. Lutfen manuel kurun: https://nodejs.org/" "Red"
    }
}
else {
    Write-Safe "[OK] Node.js surumu uyumlu." "Green"
}

# 5.2 Python SSL Testi
Write-Safe "[ISLEM] Python SSL modulu test ediliyor..." "Yellow"
$SslTest = & $PythonExe -c "import ssl; print(ssl.OPENSSL_VERSION)" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Safe "[HATA] Python SSL modulu yuklenemedi!" "Red"
    Write-Safe "Detay: $SslTest" "Gray"
    $TrustedHost = "--trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host bootstrap.pypa.io"
}
else {
    Write-Safe "[OK] SSL Modulu Hazir: $SslTest" "Green"
    $TrustedHost = ""
}

# 5.2 Pip Guncelleme ve Kurulum
Write-Safe "[ISLEM] Pip guncelleniyor..." "Yellow"
& $PythonExe -m pip install --upgrade pip $TrustedHost --no-warn-script-location 2>&1 | Write-Safe

Write-Safe "[ISLEM] requirements.txt kuruluyor..." "Yellow"
# Verbose cikti verelim ki kullanıcı hatayı gorsun
Write-Safe "> Detayli cikti aktif edildi..." "Gray"

# requirements.txt kurulumunu try-catch ve detayli cikti ile yapalim
Invoke-Expression "& `"$PythonExe`" -m pip install -r requirements.txt $TrustedHost --no-warn-script-location"

if ($LASTEXITCODE -ne 0) {
    Write-Safe "`n[HATA] Bagimliliklar kurulurken bir hata olustu!" "Red"
    Write-Safe "[TIP] Internet baglantisini kontrol edin veya firewall'u gecici olarak kapatin." "Yellow"
    Write-Safe "[TIP] Sistemde Visual C++ Redistributable (2015-2022) kurulu oldugundan emin olun." "Yellow"
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

    Write-Safe "[BILGI] API Portu doluysa otomatik olarak bir sonraki musait port secilecektir." "Cyan"
    Write-Safe "[BASARILI] Kurulum sihirbazi baslatiliyor..." "Green"
    # Launch start_setup.py via portable python
    Start-Process -FilePath $PythonPath -ArgumentList "`"$SetupScript`" --mode $choice" -WorkingDirectory $TargetDir -WindowStyle Hidden
}
else {
    Write-Safe "[HATA] start_setup.py bulunamadi!" "Red"
    pause
}
