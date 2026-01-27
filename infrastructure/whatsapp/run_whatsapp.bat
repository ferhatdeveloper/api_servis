@echo off
set LOG_FILE="d:\Developer\App\EXFIN_OPS\backend\infrastructure\whatsapp\service_startup_debug.log"
echo [%date% %time%] --- WRAPPER START --- >> %LOG_FILE%
echo [%date% %time%] Current User: %USERNAME% >> %LOG_FILE%
echo [%date% %time%] Working Dir: %CD% >> %LOG_FILE%
cd /d "d:\Developer\App\EXFIN_OPS\backend\infrastructure\whatsapp"
echo [%date% %time%] Adjusted Dir: %CD% >> %LOG_FILE%
set PATH=C:\Program Files\nodejs;%PATH%
echo [%date% %time%] Running Node... >> %LOG_FILE%
"C:\Program Files\nodejs\node.exe" dist\main.js >> %LOG_FILE% 2>&1
