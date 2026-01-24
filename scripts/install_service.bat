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

:: 1. Python Sürümü Belirle (Portable Öncelikli)
if exist "python\python.exe" (
    set PY_DIR=%~dp0\..\python
    set PYTHON_EXE=%~dp0\..\python\python.exe
    set "PATH=%~dp0\..\python;%~dp0\..\python\Scripts;%PATH%"
) else if exist "venv\Scripts\python.exe" (
    set PY_DIR=%~dp0\..\venv\Scripts
    set PYTHON_EXE=%~dp0\..\venv\Scripts\python.exe
    set "PATH=%~dp0\..\venv\Scripts;%PATH%"
) else (
    echo [HATA] Python bulunamadı!
    pause
    exit /b 1
)

:: 2. Branded Runner Kontrolü
if not exist "%PY_DIR%\ExfinOpsService.exe" (
    echo [BILGI] Branded runner oluşturuluyor...
    copy /y "%PYTHON_EXE%" "%PY_DIR%\ExfinOpsService.exe" >nul
)
set SERVICE_RUNNER=%PY_DIR%\ExfinOpsService.exe

:: 3. Servis dosyasını ve bağımlılıklarını kontrol et
if not exist "scripts\windows_service.py" (
    echo [HATA] scripts\windows_service.py bulunamadı!
    pause
    exit /b 1
)

:: 4. Servis Adı Belirle
set SVC_NAME=Exfin_ApiService
sc query %SVC_NAME% >nul 2>&1
if %errorlevel% equ 0 (
    echo [UYARI] '%SVC_NAME%' adinda bir servis zaten mevcut!
    set /p NEW_NAME="Yeni servis adini girin (Bos birakirsa mevcut guncellenir): "
    if not "%NEW_NAME%"=="" (
        set SVC_NAME=%NEW_NAME%
        echo [BILGI] Yeni servis adi: %SVC_NAME%
        "%PYTHON_EXE%" -c "import sqlite3; db='api.db'; conn=sqlite3.connect(db); conn.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)'); conn.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (''ServiceName'', ?)', ('%SVC_NAME%',)); conn.commit(); conn.close()"
    )
)

:: 5. Servisi yukle
echo [BILGI] Servis kaydediliyor (%SVC_NAME%)...
"%SERVICE_RUNNER%" "scripts\windows_service.py" --startup auto install

if %errorlevel% neq 0 (
    echo [HATA] Servis yuklenemedi. (Belki zaten yukludur? --update deneyebilirsiniz)
) else (
    echo [BASARILI] Servis basariyla yuklendi.
    echo [BILGI] Servis baslatiliyor...
    "%SERVICE_RUNNER%" "scripts\windows_service.py" start
)

echo.
echo ==========================================
echo Islem tamamlandi.
pause
