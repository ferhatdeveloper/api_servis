# EXFIN OPS - Kurulum Politikası Düzeltici v2.3 (Ultra-Aggressive Fix)
# Bu script, fatal 0x80070643 ve 0x80070659 hatalarını aşmak için tasarlanmıştır.

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
Write-Host "    SİSTEM KURULUM POLİTİKASI DÜZELTİCİ" -ForegroundColor Cyan
Write-Host "==========================================`n" -ForegroundColor Cyan

if (!([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "[HATA] Lütfen bu scripti 'YÖNETİCİ OLARAK' çalıştırın!" -ForegroundColor Red
    pause
    return
}

$fixed = $false

# 1. Çalışan Tüm Yükleyicileri Temizle
Write-Host "[>] Çalışan yükleme süreçleri temizleniyor..." -ForegroundColor White
Get-Process msiexec | Stop-Process -Force
Get-Process python* | Stop-Process -Force

# 2. MSI Lock ve InProgress Kayıtlarını Temizle
Write-Host "[>] MSI kilitleri ve yarım kalan kurulumlar temizleniyor..." -ForegroundColor White

# InProgress temizle
if (Test-Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Installer\InProgress") {
    Remove-Item -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Installer\InProgress" -Recurse -Force
    Write-Host "[+] MSI InProgress kilidi kaldırıldı." -ForegroundColor Green
    $fixed = $true
}

# PendingFileRenameOperations temizle
if (Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager" -Name "PendingFileRenameOperations" -ErrorAction SilentlyContinue) {
    Remove-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager" -Name "PendingFileRenameOperations" -Force
    Write-Host "[+] Bekleyen dosya işlemleri sıfırlandı." -ForegroundColor Green
    $fixed = $true
}

# 3. Windows Installer Servisini Sıfırla (Reregister)
Write-Host "[>] Windows Installer servisi yeniden kaydediliyor..." -ForegroundColor White
& msiexec /unreg
& msiexec /regserver
Set-Service -Name "msiserver" -StartupType Manual
Restart-Service -Name "msiserver"

function Resolve-RegistryRestriction {
    param($Path, $Name, $AlwaysSetTo = $null)
    if (!(Test-Path $Path)) { New-Item -Path $Path -Force | Out-Null }
    
    $current = Get-ItemProperty -Path $Path -Name $Name -ErrorAction SilentlyContinue
    if ($null -ne $current) {
        Write-Host "[!] Kısıtlama anahtarı bulundu: $Name ($Path)" -ForegroundColor Yellow
        if ($null -ne $AlwaysSetTo) {
            Set-ItemProperty -Path $Path -Name $Name -Value $AlwaysSetTo -Force
            Write-Host "[+] Değer $AlwaysSetTo olarak güncellendi." -ForegroundColor Green
        }
        else {
            Remove-ItemProperty -Path $Path -Name $Name -Force
            Write-Host "[-] Kısıtlama silindi." -ForegroundColor Green
        }
        return $true
    }
    elseif ($null -ne $AlwaysSetTo) {
        New-ItemProperty -Path $Path -Name $Name -Value $AlwaysSetTo -PropertyType DWord -Force | Out-Null
        Write-Host "[+] Bypass anahtarı oluşturuldu: $Name = $AlwaysSetTo" -ForegroundColor Cyan
        return $true
    }
    return $false
}

# 4. Agresif Installer Politikaları
$paths = @(
    "HKLM:\SOFTWARE\Policies\Microsoft\Windows\Installer",
    "HKCU:\SOFTWARE\Policies\Microsoft\Windows\Installer",
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Installer\Managed",
    "HKLM:\SOFTWARE\WOW6432Node\Policies\Microsoft\Windows\Installer"
)

foreach ($p in $paths) {
    if (Resolve-RegistryRestriction -Path $p -Name "DisableMSI" -AlwaysSetTo 0) { $fixed = $true }
    if (Resolve-RegistryRestriction -Path $p -Name "DisablePatch" -AlwaysSetTo 0) { $fixed = $true }
    if (Resolve-RegistryRestriction -Path $p -Name "DisableUserInstalls" -AlwaysSetTo 0) { $fixed = $true }
    if (Resolve-RegistryRestriction -Path $p -Name "AlwaysInstallElevated" -AlwaysSetTo 1) { $fixed = $true }
    if (Resolve-RegistryRestriction -Path $p -Name "EnableAdminRemote" -AlwaysSetTo 1) { $fixed = $true }
}

if ($fixed) {
    Write-Host "`n[BAŞARILI] Politika düzeltme ve Servis sıfırlama tamamlandı." -ForegroundColor Green
}
else {
    Write-Host "`n[BİLGİ] Bypass anahtarları zaten mevcuttu, servisler sıfırlandı." -ForegroundColor Cyan
}

Write-Host "[!] ŞİMDİ Python kurulumunu tekrar deneyin." -ForegroundColor White
Write-Host "------------------------------------------" -ForegroundColor Cyan
pause
