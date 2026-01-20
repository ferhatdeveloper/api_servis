@echo off
cd /d "%~dp0\.."

REM Use explicit python path just like run_api.bat
if exist "venv\Scripts\python.exe" (
    set PYTHON_EXE=venv\Scripts\python.exe
) else (
    rem Fallback to system python if venv not found
    set PYTHON_EXE=python
)

REM Run silently in background
start /b "" "%PYTHON_EXE%" main.py > logs\startup.log 2>&1
exit
