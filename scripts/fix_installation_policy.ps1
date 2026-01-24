# EXFIN OPS - Kurulum Politikası Düzeltici (Error 0x80070659 Fix)
# Bu script, sistem politikası nedeniyle engellenen Python kurulumunu açmaya çalışır.

$ErrorActionPreference = "SilentlyContinue"
chcp 65001 >$null

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "    SİSTEM KURULUM POLİTİKASI DÜZELTİCİ" -ForegroundColor Cyan
Write-Host "==========================================`n" -ForegroundColor Cyan

# Yönetici kontrolü
if (!([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "[HATA] Lütfen bu scripti 'Yönetici Olarak' çalıştırın!" -ForegroundColor Red
    pause
    return
}

function Resolve-RegistryRestriction {
    param($Path, $Name)
    if (Test-Path $Path) {
        $val = Get-ItemProperty -Path $Path -Name $Name -ErrorAction SilentlyContinue
        if ($null -ne $val) {
            Write-Host "[!] $Name kısıtlaması bulundu ($Path). Kaldırılıyor..." -ForegroundColor Yellow
            Remove-ItemProperty -Path $Path -Name $Name -Force
            return $true
        }
    }
    return $false
}

$fixed = $false

# Yaygın kısıtlama anahtarları
$paths = @(
    "HKLM:\Software\Policies\Microsoft\Windows\Installer",
    "HKCU:\Software\Policies\Microsoft\Windows\Installer",
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Installer"
)

$names = @("DisableMSI", "DisablePatch", "DisableLUAPatch", "InstallEverywhere")

foreach ($p in $paths) {
    foreach ($n in $names) {
        if (Resolve-RegistryRestriction -Path $p -Name $n) { $fixed = $true }
    }
}

# Windows Installer Servisini Yeniden Başlat
Write-Host "[>] Windows Installer servisi kontrol ediliyor..." -ForegroundColor White
Set-Service -Name "msiserver" -StartupType Manual
Restart-Service -Name "msiserver" -ErrorAction SilentlyContinue

if ($fixed) {
    Write-Host "`n[BAŞARILI] Kısıtlamalar temizlendi. Lütfen Python kurulumunu tekrar deneyin." -ForegroundColor Green
}
else {
    Write-Host "`n[BİLGİ] Belgin bir politika kısıtlaması bulunamadı." -ForegroundColor Yellow
    Write-Host "ÖNERİ: Eğer sorun devam ediyorsa, indirdiğiniz Python dosyasını sağ tıklayıp 'Engellemeyi Kaldır' (Unblock) deyin." -ForegroundColor White
}

Write-Host "`n==========================================" -ForegroundColor Cyan
pause
