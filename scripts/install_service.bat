@echo off
setlocal enabledelayedexpansion

:: Check for admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [HATA] Lütfen bu dosyayı YÖNETİCİ olarak çalıştırın!
    pause
    exit /b 1
)

cd /d "%~dp0\.."
echo ==========================================
echo    EXFIN OPS - Windows Servis Kurulumu
echo ==========================================

:: 1. Sanal ortamı ve branded runner'ı kontrol et
if not exist "venv\Scripts\ExfinOpsService.exe" (
    echo [BILGI] Branded runner oluşturuluyor...
    if exist "venv\Scripts\python.exe" (
        copy /y "venv\Scripts\python.exe" "venv\Scripts\ExfinOpsService.exe" >nul
    ) else (
        echo [HATA] Sanal ortam (venv) bulunamadı! Lütfen önce SETUP.bat çalıştırın.
        pause
        exit /b 1
    )
)

:: 2. Servis dosyasını ve bağımlılıklarını kontrol et
if not exist "scripts\windows_service.py" (
    echo [HATA] scripts\windows_service.py bulunamadı!
    pause
    exit /b 1
)

:: 3. Servisi yükle
echo [BILGI] Servis kaydediliyor...
"venv\Scripts\ExfinOpsService.exe" "scripts\windows_service.py" --startup auto install

if %errorlevel% neq 0 (
    echo [HATA] Servis yüklenemedi. (Belki zaten yüklüdür? --update deneyebilirsiniz)
) else (
    echo [BASARILI] Servis başarıyla yüklendi.
    echo [BILGI] Servis başlatılıyor...
    "venv\Scripts\ExfinOpsService.exe" "scripts\windows_service.py" start
)

echo.
echo ==========================================
echo Islem tamamlandi.
pause
