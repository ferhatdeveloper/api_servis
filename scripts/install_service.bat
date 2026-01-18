@echo off
echo ===================================================
echo EXFIN API - Windows Servis Kurulumu
echo ===================================================
echo.
echo Lutfen bu dosyayi 'Yonetici Olarak' calistirdiginizdan emin olun.
echo.

cd /d "%~dp0\.."

echo 1. Gerekli kutuphaneler kontrol ediliyor...
venv\Scripts\python.exe -m pip install pywin32

echo.
echo 2. Servis yukleniyor (ExfinApiService)...
venv\Scripts\python.exe windows_service.py install

echo.
echo 3. Servis otomatik baslatma moduna aliniyor...
venv\Scripts\python.exe windows_service.py --startup auto update

echo.
echo 4. Servis baslatiliyor...
venv\Scripts\python.exe windows_service.py start

echo.
echo ===================================================
echo KURULUM TAMAMLANDI! 
echo Servis Adi: ExfinApiService
echo Durum: Calisiyor (Arka Planda)
echo ===================================================
echo.
pause
