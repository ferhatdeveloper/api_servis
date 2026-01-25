@echo off
setlocal
title EXFIN OPS SETUP

:: Set encoding to UTF-8
chcp 65001 > nul

echo =========================================
echo    EXFIN OPS - Baslatma Sihirbazi 🚀
echo =========================================

:: 1. Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [HATA] Python bulunamadi! Lutfen Python yukleyin.
    pause
    exit /b 1
)

:: 2. Setup Virtual Environment
if not exist venv (
    echo [BILGI] Sanal ortam olusturuluyor - venv...
    python -m venv venv
)

:: 3. Activate and Install Requirements
echo [BILGI] Bagimliliklar kontrol ediliyor...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip > nul
python -m pip install -r requirements.txt

:: 4. Start the Setup Script
echo [BASARILI] Hazirlik tamam. Uygulama baslatiliyor...
:: Start setup script without showing a permanent cmd window
:: start_setup.py will handle elevation if needed
python start_setup.py

exit /b 0
