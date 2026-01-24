# EXFIN OPS - Python Temizleme Aracı
# Bu script, sistemdeki mevcut Python kurulumlarını bulur ve kaldırmanıza yardımcı olur.

$ErrorActionPreference = "SilentlyContinue"
chcp 65001 >$null

Write-Host "==========================================" -ForegroundColor Magenta
Write-Host "     PYTHON TEMİZLEME VE KALDIRMA ARACI" -ForegroundColor Magenta
Write-Host "==========================================`n" -ForegroundColor Magenta

# Yönetici kontrolü
if (!([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "[HATA] Lütfen bu scripti 'Yönetici Olarak' çalıştırın!" -ForegroundColor Red
    pause
    return
}

function Get-PythonInstallations {
    $paths = @(
        "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*",
        "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*",
        "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*"
    )
    
    $found = Get-ItemProperty $paths | Where-Object { 
        $_.DisplayName -like "*Python*" -and $null -ne $_.UninstallString 
    } | Select-Object DisplayName, DisplayVersion, UninstallString, QuietUninstallString
    
    return $found
}

$pyList = Get-PythonInstallations

if ($pyList.Count -eq 0) {
    Write-Host "[BİLGİ] Sistemde yüklü Python sürümü bulunamadı." -ForegroundColor Yellow
}
else {
    Write-Host "[!] Aşağıdaki Python sürümleri tespit edildi:`n" -ForegroundColor Cyan
    $i = 1
    foreach ($py in $pyList) {
        Write-Host "$i) $($py.DisplayName) (Versiyon: $($py.DisplayVersion))" -ForegroundColor White
        $i++
    }
    
    Write-Host "`n[SEÇİM] Ne yapmak istersiniz?" -ForegroundColor White
    Write-Host "1) TÜMÜNÜ SESSİZCE KALDIR (Önerilen: Temiz bir kurulum için)" -ForegroundColor Yellow
    Write-Host "2) Hiçbirini kaldırma, çıkış yap" -ForegroundColor Cyan
    
    $choice = Read-Host "`nSeçiminiz (1 veya 2)"
    
    if ($choice -eq "1") {
        Write-Host "`n[İŞLEM] Kaldırma işlemi başlatılıyor... Lütfen bekleyin.`n" -ForegroundColor Yellow
        
        foreach ($py in $pyList) {
            Write-Host "[>] Kaldırılıyor: $($py.DisplayName)..." -ForegroundColor White
            
            if ($py.QuietUninstallString) {
                $cmd = $py.QuietUninstallString
            }
            else {
                # Try to make UninstallString silent
                $cmd = $py.UninstallString
                if ($cmd -like "*MsiExec.exe*") {
                    $cmd = $cmd -replace "/I", "/X"
                    $cmd = $cmd + " /quiet /norestart"
                }
                elseif ($cmd -like "*.exe*") {
                    $cmd = $cmd + " /quiet /uninstall"
                }
            }
            
            # Execute uninstall
            try {
                Start-Process cmd.exe -ArgumentList "/c $cmd" -Wait -WindowStyle Hidden
                Write-Host "[TAMAM] $($py.DisplayName) kaldırıldı." -ForegroundColor Green
            }
            catch {
                Write-Host "[HATA] $($py.DisplayName) kaldırılırken bir sorun oluştu." -ForegroundColor Red
            }
        }
        
        Write-Host "`n[BAŞARILI] Temizleme işlemi tamamlandı. Artık yeni kurulumu başlatabilirsiniz." -ForegroundColor Green
    }
    else {
        Write-Host "`n[İPTAL] İşlem kullanıcı tarafından durduruldu." -ForegroundColor Cyan
    }
}

Write-Host "==========================================" -ForegroundColor Magenta
pause
