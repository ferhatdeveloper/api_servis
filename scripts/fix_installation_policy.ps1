# EXFIN OPS - Fabrika Ayarlarina Donus v3.0 (Safety First)
# Bu script, onceki bypass islemlerini geri alir ve sistemi guvenli hale getirir.

$ErrorActionPreference = "SilentlyContinue"

# UTF-8 Zorlamasi
Try {
    chcp 65001 >$null
}
Catch {}

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "    MASAUSTU KURTARMA VE GUVENLIK MODU" -ForegroundColor Green
Write-Host "==========================================`n" -ForegroundColor Cyan

# Yönetici Kontrolu (CLM-Safe)
$IsAdmin = $false
try {
    net session >$null 2>&1
    if ($LASTEXITCODE -eq 0) { $IsAdmin = $true }
}
catch { }

if (-not $IsAdmin) {
    Write-Host "[HATA] Lutfen bu scripti 'YONETICI OLARAK' calistirin!" -ForegroundColor Red
    pause
    return
}

Write-Host "[>] Sistem ayarlari fabrika degerlerine donduruluyor..." -ForegroundColor White

# 1. UAC ve Oturum Ayarlarini Geri Yukle
$uacPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
Set-ItemProperty -Path $uacPath -Name "EnableLUA" -Value 1 -Type DWord -Force
Set-ItemProperty -Path $uacPath -Name "ConsentPromptBehaviorAdmin" -Value 5 -Type DWord -Force
Set-ItemProperty -Path $uacPath -Name "LocalAccountTokenFilterPolicy" -Value 0 -Type DWord -Force

# 2. Yazilim Kisitlama (SRP) Ayarlarini Temizle
$saferPaths = @(
    "HKLM:\SOFTWARE\Policies\Microsoft\Windows\Safer\CodeIdentifiers",
    "HKCU:\Software\Policies\Microsoft\Windows\Safer\CodeIdentifiers"
)
foreach ($s in $saferPaths) {
    if (Test-Path $s) {
        Set-ItemProperty -Path $s -Name "DefaultLevel" -Value 0 -Force
        Set-ItemProperty -Path $s -Name "AuthenticodeEnabled" -Value 1 -Force
    }
}

# 3. MSI Politikalarini Temizle
$msiPaths = @(
    "HKLM:\SOFTWARE\Policies\Microsoft\Windows\Installer",
    "HKCU:\SOFTWARE\Policies\Microsoft\Windows\Installer"
)
foreach ($m in $msiPaths) {
    if (Test-Path $m) {
        Remove-ItemProperty -Path $m -Name "DisableMSI" -Force
        Remove-ItemProperty -Path $m -Name "AlwaysInstallElevated" -Force
    }
}

# 4. Servis Temizligi
Write-Host "[>] MSI servisleri tazeleniyor..." -ForegroundColor White
& msiexec /unreg
& msiexec /regserver
Restart-Service -Name "msiserver" -ErrorAction SilentlyContinue

Write-Host "`n[BASARILI] Sistem ayarlari basariyla geri yuklendi." -ForegroundColor Green
Write-Host "[DIKKAT] Degisikliklerin tam olarak uygulanmasi icin bilgisayari YENIDEN BASLATIN." -ForegroundColor Yellow
Write-Host "------------------------------------------" -ForegroundColor Cyan
pause
