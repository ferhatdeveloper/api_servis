@echo off
setlocal enabledelayedexpansion
pushd "%~dp0"

echo ==================================================
echo       EXFIN API SYSTEM SETUP LAUNCHER
echo ==================================================
echo.

:: Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [HATA] Lutfen bu dosyayi SAG TIKLAYIP 'Yonetici Olarak Calistir' secin.
    echo.
    pause
    exit /b 1
)

echo [OK] Yonetici haklari dogrulandi.

:: Find Python
set PY_CMD=python

:: 1. Prioritize User Suggested Python 3.11 (Stability Fix)
set "STABLE_PY=C:\Users\FERHAT\AppData\Local\Programs\Python\Python311\python.exe"
if exist "%STABLE_PY%" (
    echo [BILGI] Onerilen Python 3.11 surumu bulundu ve kullaniliyor.
    set "PY_CMD=%STABLE_PY%"
) else (
    :: 2. Fallback to system python
    where python >nul 2>&1
    if !errorLevel! neq 0 (
        set PY_CMD=py
        where py >nul 2>&1
        if !errorLevel! neq 0 (
            echo [HATA] Python bulunamadi. Lutfen Python yukleyin.
            start https://www.python.org/downloads/
            pause
            exit /b 1
        )
    )
)

:: Check/Create VENV
:: FORCE CLEANUP for Python 3.11 Migration
if exist "%STABLE_PY%" (
    if exist "venv" (
        if not exist "venv\.created_with_311" (
            echo [BILGI] Python 3.11 gecisi icin eski sanal ortam temizleniyor...
            rd /s /q "venv"
        )
    )
)

if not exist "venv\Scripts\python.exe" (
    echo [BILGI] Sanal ortam venv bulunamadi, olusturuluyor...
    "%PY_CMD%" -m venv venv
    
    if exist "%STABLE_PY%" (
        echo 1 > "venv\.created_with_311"
    )

    if !errorLevel! neq 0 (
        echo [HATA] Sanal ortam olusturulamadi.
        pause
        exit /b 1
    )
)

:: Activate VENV and install dependencies
echo [BILGI] Bagimliliklar kontrol ediliyor...
call "venv\Scripts\activate.bat"
if !errorLevel! neq 0 (
    echo [HATA] Sanal ortam aktif edilemedi.
    pause
    exit /b 1
)

:: Install ALL dependencies from requirements.txt
:: Install ALL dependencies from requirements.txt
:: Install ALL dependencies from requirements.txt
if exist "requirements.txt" (
    echo [BILGI] Tum bagimliliklar requirements.txt dosyasindan yukleniyor
    python -m pip install -r requirements.txt --quiet
) else (
    echo [UYARI] requirements.txt bulunamadi - Sadece temel paketler yukleniyor
    python -m pip install psutil requests psycopg2-binary pymssql --quiet
)

if %errorLevel% neq 0 (
    echo [UYARI] Bagimlilik yuklemesinde hata olustu, yine de devam ediliyor...
)

:: Check if wizard exists
if not exist "scripts\wizard.py" (
    echo [HATA] 'scripts\wizard.py' dosyasi bulunamadi!
    pause
    exit /b 1
)

:: Launch Wizard
echo [OK] Sihirbaz baslatiliyor...
start "" "venv\Scripts\python.exe" "scripts\wizard.py"

echo.
echo [BASARILI] Kurulum penceresi acildi.
echo Bu pencereyi kapatabilirsiniz.
timeout /t 5
exit
