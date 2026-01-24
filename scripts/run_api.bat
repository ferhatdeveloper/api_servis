@echo off
cd /d "%~dp0\.."
echo [DEBUG] Script Path: %~f0
echo [DEBUG] Current Dir: %CD%
echo [DEBUG] Checking environment...

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Python executable NOT FOUND at: venv\Scripts\python.exe
    echo Current dir is: %CD%
    echo Please run SETUP.bat first.
    pause
    exit /b 1
)

echo [DEBUG] Found Python. Launching API...
set PYTHON_EXE=venv\Scripts\python.exe
if exist "venv\Scripts\ExfinOpsService.exe" (
    set PYTHON_EXE=venv\Scripts\ExfinOpsService.exe
)

"%PYTHON_EXE%" -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

if %errorlevel% neq 0 (
    echo [ERROR] Uvicorn exited with code %errorlevel%
)
pause
