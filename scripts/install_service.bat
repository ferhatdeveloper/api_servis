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

:: 3. Servis Adı Belirle
set SVC_NAME=Exfin_ApiService
sc query !SVC_NAME! >nul 2>&1
if %errorlevel% equ 0 (
    echo [UYARI] '!SVC_NAME!' adinda bir servis zaten mevcut!
    set /p NEW_NAME="Yeni servis adini girin (Bos birakirsa mevcut guncellenir): "
    if not "!NEW_NAME!"=="" (
        set SVC_NAME=!NEW_NAME!
        echo [BILGI] Yeni servis adi: !SVC_NAME!
        "venv\Scripts\python.exe" -c "import sqlite3; db='api.db'; conn=sqlite3.connect(db); conn.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)'); conn.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (''ServiceName'', ?)', ('!SVC_NAME!',)); conn.commit(); conn.close()"
    )
)

:: 4. Servisi yukle
echo [BILGI] Servis kaydediliyor (!SVC_NAME!)...
"venv\Scripts\ExfinOpsService.exe" "scripts\windows_service.py" --startup auto install

if %errorlevel% neq 0 (
    echo [HATA] Servis yuklenemedi. (Belki zaten yukludur? --update deneyebilirsiniz)
) else (
    echo [BASARILI] Servis basariyla yuklendi.
    echo [BILGI] Servis baslatiliyor...
    "venv\Scripts\ExfinOpsService.exe" "scripts\windows_service.py" start
)

echo.
echo ==========================================
echo Islem tamamlandi.
pause
