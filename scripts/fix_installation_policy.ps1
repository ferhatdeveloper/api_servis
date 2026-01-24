# EXFIN OPS - Fabrika Ayarlarına Dönüş v3.0 (Safety First)
# Bu script, önceki bypass işlemlerini geri alır ve sistemi güvenli hale getirir.

$ErrorActionPreference = "SilentlyContinue"

# UTF-8 Zorlaması
Try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    [Console]::InputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
    chcp 65001 >$null
}
Catch {}

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "    MASAÜSTÜ KURTARMA VE GÜVENLİK MODU" -ForegroundColor Green
Write-Host "==========================================`n" -ForegroundColor Cyan

if (!([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "[HATA] Lütfen bu scripti 'YÖNETİCİ OLARAK' çalıştırın!" -ForegroundColor Red
    pause
    return
}

Write-Host "[>] Sistem ayarları fabrika değerlerine döndürülüyor..." -ForegroundColor White

# 1. UAC ve Oturum Ayarlarını Geri Yükle
$uacPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
Set-ItemProperty -Path $uacPath -Name "EnableLUA" -Value 1 -Type DWord -Force
Set-ItemProperty -Path $uacPath -Name "ConsentPromptBehaviorAdmin" -Value 5 -Type DWord -Force
Set-ItemProperty -Path $uacPath -Name "LocalAccountTokenFilterPolicy" -Value 0 -Type DWord -Force

# 2. Yazılım Kısıtlama (SRP) Ayarlarını Temizle
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

# 3. MSI Politikalarını Temizle
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

# 4. Servis Temizliği
Write-Host "[>] MSI servisleri tazeleniyor..." -ForegroundColor White
& msiexec /unreg
& msiexec /regserver
Restart-Service -Name "msiserver" -ErrorAction SilentlyContinue

Write-Host "`n[BAŞARILI] Sistem ayarları başarıyla geri yüklendi." -ForegroundColor Green
Write-Host "[DİKKAT] Değişikliklerin tam olarak uygulanması için bilgisayarı YENİDEN BAŞLATIN." -ForegroundColor Yellow
Write-Host "------------------------------------------" -ForegroundColor Cyan
pause
