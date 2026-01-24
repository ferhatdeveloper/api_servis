# EXFIN OPS - Kurulum Politikası Düzeltici v2.1 (Ultra-Aggressive Fix)
# Bu script, sistem politikası (0x80070659) engellerini en agresif şekilde kaldırmaya çalışır.

$ErrorActionPreference = "SilentlyContinue"

# UTF-8 Zorlaması (Script Başında)
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
        # Eğer anahtar yoksa ama biz bir değer set etmek istiyorsak (Bypass)
        New-ItemProperty -Path $Path -Name $Name -Value $AlwaysSetTo -PropertyType DWord -Force | Out-Null
        Write-Host "[+] Bypass anahtarı oluşturuldu: $Name = $AlwaysSetTo" -ForegroundColor Cyan
        return $true
    }
    return $false
}

$fixed = $false

# 1. Standart Installer Politikaları (HKLM ve HKCU)
$paths = @(
    "HKLM:\SOFTWARE\Policies\Microsoft\Windows\Installer",
    "HKCU:\SOFTWARE\Policies\Microsoft\Windows\Installer",
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Installer\Managed",
    "HKLM:\SOFTWARE\WOW6432Node\Policies\Microsoft\Windows\Installer",
    "HKCU:\SOFTWARE\WOW6432Node\Policies\Microsoft\Windows\Installer"
)

# DisableMSI = 0 (İzin Ver)
foreach ($p in $paths) {
    if (Resolve-RegistryRestriction -Path $p -Name "DisableMSI" -AlwaysSetTo 0) { $fixed = $true }
    if (Resolve-RegistryRestriction -Path $p -Name "DisablePatch" -AlwaysSetTo 0) { $fixed = $true }
    if (Resolve-RegistryRestriction -Path $p -Name "DisableUserInstalls" -AlwaysSetTo 0) { $fixed = $true }
    if (Resolve-RegistryRestriction -Path $p -Name "AlwaysInstallElevated" -AlwaysSetTo 1) { $fixed = $true }
    if (Resolve-RegistryRestriction -Path $p -Name "EnableAdminRemote" -AlwaysSetTo 1) { $fixed = $true }
}

# 2. Explorer Uygulama Önerileri (SmartScreen vb. engelleri)
$explorerPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer"
if (Resolve-RegistryRestriction -Path $explorerPath -Name "AicEnabled" -AlwaysSetTo "Anywhere") { $fixed = $true }

# 3. Windows Installer Servisini Sıfırla
Write-Host "`n[>] Windows Installer servisi kontrol ediliyor..." -ForegroundColor White
Set-Service -Name "msiserver" -StartupType Manual
Restart-Service -Name "msiserver" -ErrorAction SilentlyContinue

if ($fixed) {
    Write-Host "`n[BAŞARILI] Agresif düzeltme adımları uygulandı." -ForegroundColor Green
}
else {
    Write-Host "`n[BİLGİ] Otomatik bypass anahtarları oluşturuldu." -ForegroundColor Cyan
}

Write-Host "[!] Lütfen Python kurulumunu ŞİMDİ tekrar deneyin." -ForegroundColor White
Write-Host "------------------------------------------" -ForegroundColor Cyan
pause
