# EXFIN OPS - Kurulum Politikası Düzeltici v2.6 (Safety & Recovery)
# Bu script, bypass işlemlerini geri almak veya kilitli masaüstünü kurtarmak içindir.

$ErrorActionPreference = "SilentlyContinue"

# UTF-8 Zorlaması
Try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    [Console]::InputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
    chcp 65001 >$null
}
Catch {}

$SafetyMode = if ($env:OPS_ARG -eq "safe-mode") { $true } else { $false }

Write-Host "`n==========================================" -ForegroundColor Cyan
if ($SafetyMode) { Write-Host "    MASAÜSTÜ KURTARMA VE GÜVENLİK MODU" -ForegroundColor Green }
else { Write-Host "    SİSTEM KURULUM POLİTİKASI DÜZELTİCİ" -ForegroundColor Cyan }
Write-Host "==========================================`n" -ForegroundColor Cyan

if (!([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "[HATA] Lütfen bu scripti 'YÖNETİCİ OLARAK' çalıştırın!" -ForegroundColor Red
    pause
    return
}

if ($SafetyMode) {
    Write-Host "[>] Güvenlik ayarları geri yükleniyor (Masaüstünü kurtar)..." -ForegroundColor White
    Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" -Name "EnableLUA" -Value 1 -Type DWord -Force
    Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" -Name "ConsentPromptBehaviorAdmin" -Value 5 -Type DWord -Force
    Write-Host "[BAŞARILI] UAC (Kullanıcı Hesabı Denetimi) tekrar açıldı." -ForegroundColor Green
    Write-Host "[!] Lütfen masaüstünü görmek için bilgisayarınızı ŞİMDİ YENİDEN BAŞLATIN." -ForegroundColor Yellow
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
    Write-Host "[+] MSI InProgress kilidi kaldırıldı." -ForegroundColor Green
    $fixed = $true
}

# 3. SRP ve UAC Bypass (Dikkat: EnableLUA=0 masaüstünü dondurabilir)
Write-Host "[>] Kurumsal bypass ayarları yapılıyor..." -ForegroundColor White
$regActions = @(
    @{ Path = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\Safer\CodeIdentifiers"; Name = "DefaultLevel"; Value = 262144 },
    @{ Path = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\Safer\CodeIdentifiers"; Name = "PolicyLevel"; Value = 0 },
    @{ Path = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"; Name = "LocalAccountTokenFilterPolicy"; Value = 1 },
    @{ Path = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"; Name = "EnableLUA"; Value = 0 },
    @{ Path = "HKLM:\SOFTWARE\Microsoft\WinTrust\Trust Providers\Software Publishing"; Name = "State"; Value = 146944 }
)

foreach ($ra in $regActions) {
    if (!(Test-Path $ra.Path)) { New-Item -Path $ra.Path -Force | Out-Null }
    Set-ItemProperty -Path $ra.Path -Name $ra.Name -Value $ra.Value -Type DWord -Force
    $fixed = $true
}

# 4. Windows Installer Servisini Sıfırla
Write-Host "[>] MSI servisi tazeleniyor..." -ForegroundColor White
& msiexec /unreg
& msiexec /regserver
Restart-Service -Name "msiserver"

Write-Host "`n[BAŞARILI] Tüm kısıtlamalar bypass edildi." -ForegroundColor Green
Write-Host "[DİKKAT] Eğer ekranınız donarsa veya masaüstü gelmezse bilgisayarı YENİDEN BAŞLATIN." -ForegroundColor Yellow
Write-Host "[!] Kuruluma yeniden başlatma sonrası devam edebilirsiniz." -ForegroundColor White
Write-Host "------------------------------------------" -ForegroundColor Cyan
pause
