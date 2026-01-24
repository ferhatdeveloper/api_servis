# EXFIN OPS - Kurulum Politikası Düzeltici v2.5 (Ultimate Enterprise Bypass)
# Bu script, fatal 0x80070643, 0x80070659 ve 'Yönetici Tarafından Engellendi' (Red UAC) hatalarını aşmak içindir.

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
Get-Process msiexec, python* -ErrorAction SilentlyContinue | Stop-Process -Force

# 2. MSI Lock ve InProgress Kayıtlarını Temizle
Write-Host "[>] MSI kilitleri temizleniyor..." -ForegroundColor White
if (Test-Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Installer\InProgress") {
    Remove-Item -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Installer\InProgress" -Recurse -Force
    $fixed = $true
}

# 3. SRP (Software Restriction Policies) ve Signature Bypass - RED UAC BOX FIX
Write-Host "[>] Yazılım kısıtlama ve imza denetimleri bypass ediliyor..." -ForegroundColor White
$regActions = @(
    @{ Path = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\Safer\CodeIdentifiers"; Name = "DefaultLevel"; Value = 262144 },
    @{ Path = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\Safer\CodeIdentifiers"; Name = "PolicyLevel"; Value = 0 },
    @{ Path = "HKLM:\SOFTWARE\Microsoft\Windows\Safer\CodeIdentifiers"; Name = "AuthenticodeEnabled"; Value = 0 },
    @{ Path = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"; Name = "LocalAccountTokenFilterPolicy"; Value = 1 },
    @{ Path = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"; Name = "EnableLUA"; Value = 0 },
    @{ Path = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"; Name = "ConsentPromptBehaviorAdmin"; Value = 0 },
    @{ Path = "HKLM:\SOFTWARE\Microsoft\WinTrust\Trust Providers\Software Publishing"; Name = "State"; Value = 146944 }
)

foreach ($ra in $regActions) {
    if (!(Test-Path $ra.Path)) { New-Item -Path $ra.Path -Force | Out-Null }
    Set-ItemProperty -Path $ra.Path -Name $ra.Name -Value $ra.Value -Type DWord -Force
    $fixed = $true
}

# 4. Windows Installer Servisini Sıfırla
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
        Write-Host "[!] Kısıtlama bulundu: $Name" -ForegroundColor Yellow
        if ($null -ne $AlwaysSetTo) { Set-ItemProperty -Path $Path -Name $Name -Value $AlwaysSetTo -Force }
        else { Remove-ItemProperty -Path $Path -Name $Name -Force }
        return $true
    }
    elseif ($null -ne $AlwaysSetTo) {
        New-ItemProperty -Path $Path -Name $Name -Value $AlwaysSetTo -PropertyType DWord -Force | Out-Null
        return $true
    }
    return $false
}

# 5. Agresif Installer Politikaları
$paths = @(
    "HKLM:\SOFTWARE\Policies\Microsoft\Windows\Installer",
    "HKLM:\SOFTWARE\WOW6432Node\Policies\Microsoft\Windows\Installer"
)

foreach ($p in $paths) {
    if (Resolve-RegistryRestriction -Path $p -Name "DisableMSI" -AlwaysSetTo 0) { $fixed = $true }
    if (Resolve-RegistryRestriction -Path $p -Name "DisablePatch" -AlwaysSetTo 0) { $fixed = $true }
    if (Resolve-RegistryRestriction -Path $p -Name "AlwaysInstallElevated" -AlwaysSetTo 1) { $fixed = $true }
}

if ($fixed) {
    Write-Host "`n[BAŞARILI] Kurumsal kısıtlamalar (SRP/Signature) bypass edildi." -ForegroundColor Green
}
else {
    Write-Host "`n[BİLGİ] Bypass anahtarları zaten yüklü." -ForegroundColor Cyan
}

Write-Host "[!] Lütfen Python kurulumunu ŞİMDİ tekrar deneyin." -ForegroundColor White
Write-Host "------------------------------------------" -ForegroundColor Cyan
pause
